import 'package:dio/dio.dart';

import 'app_error.dart';
import 'config.dart';
import 'token_storage.dart';

/// Central HTTP client for the Flood Risk DSS backend.
///
/// - Attaches the JWT access token to every request.
/// - On 401, attempts a single refresh-token rotation and retries once.
/// - Maps Dio/network failures to typed [AppException]s so the UI can render
///   consistent loading / error / empty states.
class ApiClient {
  ApiClient({
    Dio? dio,
    TokenStorage? tokenStorage,
    String? baseUrl,
    Future<Map<String, String>> Function()? refreshHook,
  })  : _dio = dio ?? Dio(),
        _tokenStorage = tokenStorage ?? TokenStorage(),
        _refreshHook = refreshHook {
    _dio.options.baseUrl = baseUrl ?? AppConfig.apiBaseUrl;
    _dio.options.connectTimeout = AppConfig.connectTimeout;
    _dio.options.receiveTimeout = AppConfig.receiveTimeout;
    _dio.options.headers['Content-Type'] = 'application/json';
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _tokenStorage.readAccessToken();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (error, handler) async {
        if (_isRefreshable(error) && !_refreshInFlight) {
          _refreshInFlight = true;
          try {
            final ok = await _tryRefresh();
            _refreshInFlight = false;
            if (ok) {
              final opts = error.requestOptions;
              final token = await _tokenStorage.readAccessToken();
              opts.headers['Authorization'] = 'Bearer $token';
              final retry = await _dio.fetch(opts);
              return handler.resolve(retry);
            }
          } catch (_) {
            _refreshInFlight = false;
          }
        }
        handler.reject(error);
      },
    ));
  }

  final Dio _dio;
  final TokenStorage _tokenStorage;
  final Future<Map<String, String>> Function()? _refreshHook;
  bool _refreshInFlight = false;

  bool _isRefreshable(DioException error) {
    final status = error.response?.statusCode;
    final path = error.requestOptions.path;
    return status == 401 && !path.endsWith('/auth/refresh') && !path.endsWith('/auth/login');
  }

  /// Exchange the stored refresh token for a new pair.
  Future<bool> _tryRefresh() async {
    final refreshToken = await _tokenStorage.readRefreshToken();
    if (refreshToken == null) return false;
    if (_refreshHook != null) {
      final pair = await _refreshHook();
      await _tokenStorage.updateAccessToken(pair['access']!, pair['refresh']!);
      return true;
    }
    try {
      // Uses the same Dio instance (and its test adapter) — the error
      // interceptor skips refresh for '/auth/refresh' itself, so this
      // cannot recurse.
      final res = await _dio.post(
        '/auth/refresh',
        data: {'refresh_token': refreshToken},
      );
      final data = res.data as Map<String, dynamic>;
      await _tokenStorage.updateAccessToken(
        data['access_token'] as String,
        (data['refresh_token'] as String?) ?? refreshToken,
      );
      return true;
    } catch (_) {
      return false;
    }
  }

  Never _mapError(DioException e) {
    final status = e.response?.statusCode;
    final data = e.response?.data;
    String detail = 'Request failed';
    if (data is Map<String, dynamic>) {
      final d = data['detail'];
      if (d is String) detail = d;
      if (d is List && d.isNotEmpty && d.first is Map) {
        detail = (d.first as Map)['msg']?.toString() ?? detail;
      }
    }
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
      case DioExceptionType.sendTimeout:
      case DioExceptionType.receiveTimeout:
      case DioExceptionType.connectionError:
        throw const NetworkException();
      case DioExceptionType.badResponse:
        if (status == 401) throw const UnauthorizedException();
        if (status == 404) throw NotFoundException(detail);
        if (status == 422 || status == 400) throw ValidationException(detail, status);
        throw AppException(detail, status);
      default:
        throw AppException(detail, status);
    }
  }

  Future<dynamic> get(String path, {Map<String, dynamic>? query}) async {
    try {
      final res = await _dio.get(path, queryParameters: query);
      return res.data;
    } on DioException catch (e) {
      _mapError(e);
    }
  }

  Future<dynamic> post(String path, {Object? data, Map<String, dynamic>? query}) async {
    try {
      final res = await _dio.post(path, data: data, queryParameters: query);
      return res.data;
    } on DioException catch (e) {
      _mapError(e);
    }
  }

  Future<dynamic> delete(String path, {Map<String, dynamic>? query}) async {
    try {
      final res = await _dio.delete(path, queryParameters: query);
      return res.data;
    } on DioException catch (e) {
      _mapError(e);
    }
  }
}
