/// Typed application errors surfaced from the API layer.
class AppException implements Exception {
  final String message;
  final int? statusCode;

  const AppException(this.message, [this.statusCode]);

  @override
  String toString() => message;
}

class UnauthorizedException extends AppException {
  const UnauthorizedException([super.message = 'Session expired. Please sign in again.']);
}

class NetworkException extends AppException {
  const NetworkException([super.message = 'No network connection. Showing cached data where available.']);
}

class NotFoundException extends AppException {
  const NotFoundException([super.message = 'Not found.']);
}

class ValidationException extends AppException {
  const ValidationException(super.message, [super.statusCode]);
}
