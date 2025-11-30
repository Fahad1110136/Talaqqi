"""
Tajweed Analysis Service - Integrates ML facade with Flask/SQLAlchemy.
Demonstrates: Service Layer Pattern, Single Responsibility, Facade integration.
"""
from typing import Dict, List, Optional
import os
from datetime import datetime
import logging

from models import db, RecitationAnalysis, TajweedError, StudentProgress, User
from utils.exceptions import AudioProcessingError, ClassificationError

# Import ML components (will work once copied from FastAPI)
try:
    from ml.facades.tajweed_analyzer import TajweedAnalyzer
except ImportError:
    # Graceful fallback during development
    TajweedAnalyzer = None
    logging.warning("TajweedAnalyzer not available - ML features disabled")

logger = logging.getLogger(__name__)


class TajweedAnalysisService:
    """
    Service for orchestrating Tajweed analysis workflow.
    Bridges ML components with Flask/SQLAlchemy database.
    
    Single Responsibility: Coordinate audio analysis and persistence.
    """
    
    def __init__(self):
        """Initialize service with ML analyzer."""
        if TajweedAnalyzer:
            self.analyzer = TajweedAnalyzer()
            logger.info("TajweedAnalysisService initialized with ML analyzer")
        else:
            self.analyzer = None
            logger.warning("TajweedAnalysisService initialized WITHOUT ML analyzer")
    
    def analyze_audio_file(self, file_path: str, student_id: int, session_id: Optional[int] = None) -> Dict:
        """
        Analyze audio file and save results to database.
        
        Args:
            file_path: Path to audio file
            student_id: Student ID from session
            session_id: Optional video call session ID
            
        Returns:
            Dict: Analysis results with database IDs
            
        Raises:
            AudioProcessingError: If analysis fails
        """
        if not self.analyzer:
            raise AudioProcessingError("ML analyzer not initialized")
        
        try:
            # Run ML analysis
            logger.info(f"Analyzing audio file: {file_path} for student {student_id}")
            ml_result = self.analyzer.analyze_audio_file(file_path)
            
            # Create RecitationAnalysis record
            analysis = RecitationAnalysis(
                student_id=student_id,
                session_id=session_id,
                audio_file_path=file_path,
                overall_score=ml_result['overall_score']
            )
            db.session.add(analysis)
            db.session.flush()  # Get ID without committing
            
            # Save Tajweed errors
            for detection in ml_result['detections']:
                error = TajweedError(
                    analysis_id=analysis.id,
                    rule_type=detection['rule_name'],
                    timestamp_in_audio=detection['timestamp'],
                    error_description=detection['description'],
                    correction_suggestion=detection.get('correction_suggestion'),
                    confidence_score=detection['confidence']
                )
                db.session.add(error)
            
            # Update student progress
            self._update_student_progress(student_id, ml_result['detections'])
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"Analysis saved with ID {analysis.id}, found {len(ml_result['detections'])} issues")
            
            # Return enriched result
            return {
                'analysis_id': analysis.id,
                'overall_score': ml_result['overall_score'],
                'detections': ml_result['detections'],
                'feedback': ml_result['feedback'],
                'predictions': ml_result.get('predictions', {})
            }
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Analysis failed: {str(e)}")
            raise AudioProcessingError(f"Failed to analyze audio: {str(e)}")
    
    def analyze_audio_stream(self, audio_data, student_id: int, room_id: str) -> Dict:
        """
        Analyze streaming audio chunk (for real-time WebSocket).
        Does not save to database - only returns results.
        
        Args:
            audio_data: Audio array (numpy)
            student_id: Student ID
            room_id: Video call room ID
            
        Returns:
            Dict: Real-time analysis results
        """
        if not self.analyzer:
            return {'error': 'ML analyzer not available'}
        
        try:
            result = self.analyzer.analyze_audio_stream(audio_data)
            logger.debug(f"Stream analysis for student {student_id} in room {room_id}")
            return result
        except Exception as e:
            logger.error(f"Stream analysis failed: {str(e)}")
            return {'error': str(e)}
    
    def get_analysis_by_id(self, analysis_id: int, student_id: Optional[int] = None) -> Optional[Dict]:
        """
        Retrieve analysis results by ID.
        
        Args:
            analysis_id: Analysis record ID
            student_id: Optional student ID for authorization check
            
        Returns:
            Dict: Analysis data or None
        """
        query = RecitationAnalysis.query.filter_by(id=analysis_id)
        
        if student_id:
            query = query.filter_by(student_id=student_id)
        
        analysis = query.first()
        
        if not analysis:
            return None
        
        return analysis.to_dict()
    
    def get_student_history(self, student_id: int, limit: int = 10) -> List[Dict]:
        """
        Get student's analysis history.
        
        Args:
            student_id: Student ID
            limit: Max number of results
            
        Returns:
            List[Dict]: Analysis records
        """
        analyses = RecitationAnalysis.query.filter_by(
            student_id=student_id
        ).order_by(
            RecitationAnalysis.timestamp.desc()
        ).limit(limit).all()
        
        return [a.to_dict() for a in analyses]
    
    def get_student_progress(self, student_id: int) -> List[Dict]:
        """
        Get student's progress on Tajweed rules.
        
        Args:
            student_id: Student ID
            
        Returns:
            List[Dict]: Progress records
        """
        progress = StudentProgress.query.filter_by(
            student_id=student_id
        ).order_by(
            StudentProgress.mastery_level.desc()
        ).all()
        
        return [p.to_dict() for p in progress]
    
    def _update_student_progress(self, student_id: int, detections: List[Dict]) -> None:
        """
        Update student progress based on analysis results.
        
        Args:
            student_id: Student ID
            detections: List of Tajweed rule detections
        """
        # For now, assume Al-Ma'idah:109 (hardcoded for POC)
        surah_name = "Al-Ma'idah"
        ayah_number = 109
        
        # Group detections by rule type
        rule_counts = {}
        for detection in detections:
            rule_type = detection['rule_name']
            rule_counts[rule_type] = rule_counts.get(rule_type, 0) + 1
        
        # Update or create progress records
        for rule_type in ['madd', 'ghunnah', 'ikhfa']:
            progress = StudentProgress.query.filter_by(
                student_id=student_id,
                surah_name=surah_name,
                ayah_number=ayah_number,
                tajweed_rule=rule_type
            ).first()
            
            if not progress:
                progress = StudentProgress(
                    student_id=student_id,
                    surah_name=surah_name,
                    ayah_number=ayah_number,
                    tajweed_rule=rule_type
                )
                db.session.add(progress)
            
            # Update metrics
            progress.practice_count += 1
            progress.last_practiced_at = datetime.utcnow()
            
            # Calculate mastery (simple heuristic - improve with actual logic)
            errors_count = rule_counts.get(rule_type, 0)
            if errors_count == 0:
                progress.mastery_level = min(100, progress.mastery_level + 5)
            else:
                progress.mastery_level = max(0, progress.mastery_level - errors_count * 2)
            
            logger.debug(f"Updated progress for {rule_type}: mastery={progress.mastery_level}%")
    
    def delete_analysis(self, analysis_id: int, student_id: Optional[int] = None) -> bool:
        """
        Delete analysis record.
        
        Args:
            analysis_id: Analysis ID
            student_id: Optional student ID for authorization
            
        Returns:
            bool: Success status
        """
        query = RecitationAnalysis.query.filter_by(id=analysis_id)
        
        if student_id:
            query = query.filter_by(student_id=student_id)
        
        analysis = query.first()
        
        if not analysis:
            return False
        
        # Delete audio file
        if os.path.exists(analysis.audio_file_path):
            try:
                os.remove(analysis.audio_file_path)
            except Exception as e:
                logger.warning(f"Failed to delete audio file: {str(e)}")
        
        # Delete from database (cascade will delete errors)
        db.session.delete(analysis)
        db.session.commit()
        
        logger.info(f"Deleted analysis {analysis_id}")
        return True
