"""
Celery task status monitoring utilities.
Useful for tracking async task progress in views.
"""
from celery.result import AsyncResult
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods


def get_task_status(task_id: str) -> dict:
    """
    Get the status of an async task.
    
    Args:
        task_id: The task ID returned by celery task
    
    Returns:
        Dictionary with task status information
    """
    result = AsyncResult(task_id)
    
    status_data = {
        'task_id': task_id,
        'state': result.state,
        'current': 0,
        'total': 100,
        'status': 'Pending...',
        'result': None
    }
    
    if result.state == 'PENDING':
        status_data['status'] = 'Task pending...'
    elif result.state == 'PROGRESS':
        status_data['current'] = result.info.get('current', 0)
        status_data['total'] = result.info.get('total', 100)
        status_data['status'] = result.info.get('status', 'Processing...')
    elif result.state == 'SUCCESS':
        status_data['current'] = 100
        status_data['total'] = 100
        status_data['status'] = 'Task succeeded'
        status_data['result'] = result.result
    elif result.state == 'FAILURE':
        status_data['status'] = f'Task failed: {str(result.info)}'
        status_data['error'] = str(result.info)
    
    return status_data


@require_http_methods(["GET"])
def task_status_view(request, task_id: str):
    """
    API endpoint to check task status.
    
    Usage:
        GET /api/tasks/{task_id}/status/
    
    Response:
        {
            "task_id": "abc123...",
            "state": "SUCCESS",
            "current": 100,
            "total": 100,
            "status": "Task succeeded",
            "result": {...}
        }
    """
    status = get_task_status(task_id)
    return JsonResponse(status)


def revoke_task(task_id: str, terminate: bool = False) -> bool:
    """
    Revoke (cancel) a running task.
    
    Args:
        task_id: The task ID to revoke
        terminate: If True, forcefully terminate; if False, wait for task to complete
    
    Returns:
        True if revoked successfully
    """
    result = AsyncResult(task_id)
    result.revoke(terminate=terminate)
    return True


def retry_task(task_id: str) -> dict:
    """
    Retry a failed task.
    
    Args:
        task_id: The task ID to retry
    
    Returns:
        Information about the retry
    """
    result = AsyncResult(task_id)
    
    if result.state == 'FAILURE':
        # In practice, you'd reconstruct the original task with its arguments
        # This is a simplified example
        return {
            'status': 'retry_attempted',
            'original_state': result.state,
            'note': 'Manual retry - implement task reconstruction for automatic retry'
        }
    
    return {
        'status': 'error',
        'message': 'Task is not in failed state'
    }
