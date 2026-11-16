"""
PDF Book API Views

REST API endpoints for PDF book management, upload, and reading functionality.
"""

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.http import FileResponse, HttpResponse
from django.core.exceptions import ValidationError

from accounts.models import Book, UserReadingSession, UserBookmark
from accounts.serializers import (
    UserReadingSessionSerializer, 
    UserBookmarkSerializer,
    BookDetailWithPDFSerializer
)
from accounts.services.pdf_manager import PDFManager, ReadingProgressManager


class IsPDFOwnerOrAdmin(permissions.BasePermission):
    """Permission to ensure only book owner or admin can upload/manage PDFs."""
    
    def has_permission(self, request, view):
        # Allow read operations for authenticated users
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        # Allow writes only for staff/admin
        return request.user and request.user.is_staff


class PDFBookViewSet(viewsets.ModelViewSet):
    """ViewSet for PDF book management."""
    
    queryset = Book.objects.filter(pdf_file__isnull=False)
    serializer_class = BookDetailWithPDFSerializer
    parser_classes = (MultiPartParser, FormParser)
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'slug'
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def pdf(self, request, slug=None):
        """
        Serve PDF file for reading.
        
        GET /api/books/{slug}/pdf/
        """
        book = self.get_object()
        
        if not PDFManager.has_book_pdf(book):
            return Response(
                {'error': 'This book does not have a PDF available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Open and serve the PDF file
        try:
            pdf_file = book.pdf_file.open('rb')
            response = FileResponse(
                pdf_file,
                content_type='application/pdf',
                as_attachment=False
            )
            response['Content-Disposition'] = f'inline; filename="{book.slug}.pdf"'
            return response
        except Exception as e:
            return Response(
                {'error': f'Error serving PDF: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def pdf_download(self, request, slug=None):
        """
        Download PDF file.
        
        GET /api/books/{slug}/pdf_download/
        """
        book = self.get_object()
        
        if not PDFManager.has_book_pdf(book):
            return Response(
                {'error': 'PDF not available'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            pdf_file = book.pdf_file.open('rb')
            response = FileResponse(
                pdf_file,
                content_type='application/pdf',
                as_attachment=True
            )
            response['Content-Disposition'] = f'attachment; filename="{book.slug}.pdf"'
            return response
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'], permission_classes=[IsPDFOwnerOrAdmin])
    def upload_pdf(self, request, slug=None):
        """
        Upload PDF file for a book (Admin only).
        
        POST /api/books/{slug}/upload_pdf/
        """
        book = self.get_object()
        
        if 'pdf_file' not in request.FILES:
            return Response(
                {'error': 'No PDF file provided'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        pdf_file = request.FILES['pdf_file']
        
        try:
            PDFManager.validate_pdf_file(pdf_file)
            book = PDFManager.upload_pdf_to_book(book, pdf_file)
            
            return Response(
                {
                    'message': 'PDF uploaded successfully',
                    'book': BookDetailWithPDFSerializer(
                        book,
                        context={'request': request}
                    ).data
                },
                status=status.HTTP_200_OK
            )
        except ValueError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Upload failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['delete'], permission_classes=[IsPDFOwnerOrAdmin])
    def delete_pdf(self, request, slug=None):
        """
        Delete PDF file from a book (Admin only).
        
        DELETE /api/books/{slug}/delete_pdf/
        """
        book = self.get_object()
        
        if not book.pdf_file:
            return Response(
                {'error': 'No PDF file to delete'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        try:
            book.pdf_file.delete(save=False)
            book.pdf_uploaded_at = None
            book.save(update_fields=['pdf_file', 'pdf_uploaded_at'])
            
            return Response(
                {'message': 'PDF deleted successfully'},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ReadingSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for reading session management."""
    
    serializer_class = UserReadingSessionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's reading sessions."""
        return UserReadingSession.objects.filter(user=self.request.user)
    
    def create(self, request, *args, **kwargs):
        """Create or get reading session for a book."""
        book_id = request.data.get('book')
        
        if not book_id:
            return Response(
                {'error': 'book ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        book = get_object_or_404(Book, id=book_id)
        session, created = ReadingProgressManager.get_or_create_reading_session(
            request.user, book
        )
        
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def update_progress(self, request, pk=None):
        """
        Update reading progress for current user.
        
        POST /api/reading-sessions/{id}/update_progress/
        Body: {"current_page": 42, "time_spent_increment": 300}
        """
        session = self.get_object()
        
        current_page = request.data.get('current_page')
        time_spent_increment = request.data.get('time_spent_increment', 0)
        
        if current_page is None:
            return Response(
                {'error': 'current_page is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            current_page = int(current_page)
            time_spent_increment = int(time_spent_increment)
        except (ValueError, TypeError):
            return Response(
                {'error': 'current_page and time_spent_increment must be integers'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session = ReadingProgressManager.update_reading_progress(
            request.user,
            session.book,
            current_page,
            time_spent_increment
        )
        
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def mark_completed(self, request, pk=None):
        """Mark a book as completed."""
        session = self.get_object()
        session = ReadingProgressManager.mark_book_as_completed(request.user, session.book)
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['post'])
    def mark_abandoned(self, request, pk=None):
        """Mark a book as abandoned."""
        session = self.get_object()
        session = ReadingProgressManager.mark_book_as_abandoned(request.user, session.book)
        serializer = self.get_serializer(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserBookmarkViewSet(viewsets.ModelViewSet):
    """ViewSet for user bookmarks."""
    
    serializer_class = UserBookmarkSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Return only the current user's bookmarks."""
        return UserBookmark.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Override to set the user to current user."""
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def book_bookmarks(self, request):
        """
        Get all bookmarks for a specific book.
        
        GET /api/bookmarks/book_bookmarks/?book_id=123
        """
        book_id = request.query_params.get('book_id')
        
        if not book_id:
            return Response(
                {'error': 'book_id parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        bookmarks = UserBookmark.objects.filter(
            user=request.user,
            book_id=book_id
        ).order_by('page_number')
        
        serializer = self.get_serializer(bookmarks, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def create_bookmark(self, request):
        """
        Create a bookmark.
        
        POST /api/bookmarks/create_bookmark/
        Body: {
            "book": 123,
            "page_number": 42,
            "label": "Important chapter",
            "color": "yellow",
            "bookmark_type": "bookmark"
        }
        """
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

