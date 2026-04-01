"""
PDF Book Management Service

Handles PDF file uploads, validation, serving, and reading progress tracking.
"""

import mimetypes
from pathlib import Path
from django.core.files.storage import default_storage
from django.utils import timezone
from django.conf import settings
from accounts.models import Book, UserReadingSession, UserBookmark


class PDFManager:
    """Manages PDF book uploads and operations."""
    
    ALLOWED_EXTENSIONS = {'pdf'}
    MAX_FILE_SIZE = settings.MAX_UPLOAD_SIZE  # 100MB
    
    @staticmethod
    def validate_pdf_file(file_obj):
        """Validate if uploaded file is a valid PDF."""
        # Check file extension
        if file_obj.name.lower().split('.')[-1] not in PDFManager.ALLOWED_EXTENSIONS:
            raise ValueError("File must be a PDF (.pdf extension)")
        
        # Check file size
        if file_obj.size > PDFManager.MAX_FILE_SIZE:
            raise ValueError(
                f"File size {file_obj.size / 1024 / 1024:.1f}MB exceeds maximum "
                f"{PDFManager.MAX_FILE_SIZE / 1024 / 1024:.0f}MB"
            )
        
        # Check MIME type
        mime_type, _ = mimetypes.guess_type(file_obj.name)
        if mime_type not in ['application/pdf']:
            raise ValueError(f"Invalid MIME type: {mime_type}. Expected application/pdf")
        
        return True
    
    @staticmethod
    def upload_pdf_to_book(book: Book, pdf_file, user_id=None):
        """
        Upload PDF file to a book.
        
        Args:
            book: Book instance to upload PDF to
            pdf_file: File object from request
            user_id: Optional user ID performing upload (for permissions check)
            
        Returns:
            Book instance with updated PDF file
            
        Raises:
            ValueError: If file validation fails
        """
        if not PDFManager.validate_pdf_file(pdf_file):
            raise ValueError("PDF validation failed")
        
        book.pdf_file = pdf_file
        book.pdf_uploaded_at = timezone.now()
        book.save(update_fields=['pdf_file', 'pdf_uploaded_at'])
        
        return book
    
    @staticmethod
    def get_book_pdf_url(book: Book, request=None):
        """Get URL to serve PDF for a book."""
        if not book.pdf_file:
            return None
        
        if request:
            return request.build_absolute_uri(book.pdf_file.url)
        return book.pdf_file.url
    
    @staticmethod
    def has_book_pdf(book: Book) -> bool:
        """Check if book has a PDF file."""
        return bool(book.pdf_file)


class ReadingProgressManager:
    """Manages user reading progress, bookmarks, and session data."""
    
    @staticmethod
    def get_or_create_reading_session(user, book):
        """Get or create a reading session for user-book pair."""
        session, created = UserReadingSession.objects.get_or_create(
            user=user,
            book=book,
            defaults={
                'current_page': 0,
                'progress_percentage': 0,
                'status': 'not_started',
                'time_spent': 0,
            }
        )
        return session, created
    
    @staticmethod
    def update_reading_progress(user, book, current_page: int, time_spent_increment: int = 0):
        """
        Update reading progress for a user on a book.
        
        Args:
            user: User instance
            book: Book instance
            current_page: Current page number
            time_spent_increment: Time to add to total reading time (in seconds)
            
        Returns:
            Updated UserReadingSession instance
        """
        session, _ = UserReadingSession.objects.get_or_create(
            user=user,
            book=book,
            defaults={
                'current_page': 0,
                'progress_percentage': 0,
                'status': 'not_started',
                'time_spent': 0,
            }
        )
        
        session.current_page = current_page
        
        # Update progress percentage if total_pages is known
        if session.total_pages and session.total_pages > 0:
            session.progress_percentage = (current_page / session.total_pages) * 100
        
        # Update status based on page
        if current_page > 0 and session.status == 'not_started':
            session.status = 'in_progress'
        elif session.total_pages and current_page >= session.total_pages:
            session.status = 'completed'
        
        # Accumulate time spent
        if time_spent_increment > 0:
            session.time_spent += time_spent_increment
        
        session.save()
        return session
    
    @staticmethod
    def get_user_reading_session(user, book):
        """Get reading session for user-book pair."""
        try:
            return UserReadingSession.objects.get(user=user, book=book)
        except UserReadingSession.DoesNotExist:
            return None
    
    @staticmethod
    def create_bookmark(user, book, page_number: int, label: str = "", 
                       color: str = "yellow", bookmark_type: str = "bookmark"):
        """
        Create a bookmark for user on specific page.
        
        Args:
            user: User instance
            book: Book instance
            page_number: Page to bookmark
            label: Optional label/note
            color: Color for visual organization
            bookmark_type: Type of bookmark (bookmark, note, highlight)
            
        Returns:
            UserBookmark instance
        """
        bookmark = UserBookmark.objects.create(
            user=user,
            book=book,
            page_number=page_number,
            label=label,
            color=color,
            bookmark_type=bookmark_type
        )
        return bookmark
    
    @staticmethod
    def get_user_bookmarks(user, book):
        """Get all bookmarks for user on a book."""
        return UserBookmark.objects.filter(
            user=user,
            book=book
        ).order_by('page_number')
    
    @staticmethod
    def delete_bookmark(user, bookmark_id):
        """Delete a bookmark."""
        try:
            bookmark = UserBookmark.objects.get(id=bookmark_id, user=user)
            bookmark.delete()
            return True
        except UserBookmark.DoesNotExist:
            return False
    
    @staticmethod
    def get_user_reading_list(user):
        """Get all books user is reading or has read."""
        return UserReadingSession.objects.filter(user=user).order_by('-last_read_at')
    
    @staticmethod
    def get_user_completed_books(user):
        """Get all books user has completed."""
        return UserReadingSession.objects.filter(
            user=user,
            status='completed'
        ).order_by('-updated_at')
    
    @staticmethod
    def mark_book_as_completed(user, book):
        """Mark a book as completed."""
        session, _ = UserReadingSession.objects.get_or_create(user=user, book=book)
        session.status = 'completed'
        if session.total_pages:
            session.current_page = session.total_pages
            session.progress_percentage = 100
        session.save()
        return session
    
    @staticmethod
    def mark_book_as_abandoned(user, book):
        """Mark a book as abandoned."""
        session, _ = UserReadingSession.objects.get_or_create(user=user, book=book)
        session.status = 'abandoned'
        session.save()
        return session

