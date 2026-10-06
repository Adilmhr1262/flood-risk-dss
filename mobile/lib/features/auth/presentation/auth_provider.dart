import 'package:flutter/foundation.dart';

import '../../../core/api_client.dart';
import '../../../core/cache_service.dart';
import '../../../core/token_storage.dart';
import '../data/auth_repository.dart';

/// Session state for the whole app. Provided above MaterialApp so the router
/// can switch between the auth flow and the main tab shell.
class AuthProvider extends ChangeNotifier {
  AuthProvider({ApiClient? api, TokenStorage? tokens, CacheService? cache})
      : _api = api ?? ApiClient(),
        _tokens = tokens ?? TokenStorage(),
        _cache = cache ?? CacheService();

  final ApiClient _api;
  final TokenStorage _tokens;
  final CacheService _cache;

  late final AuthRepository _repo = AuthRepository(api: _api, tokens: _tokens);

  UserProfile? _user;
  bool _initializing = true;
  bool _busy = false;
  String? _error;

  UserProfile? get user => _user;
  bool get isSignedIn => _user != null;
  bool get initializing => _initializing;
  bool get busy => _busy;
  String? get error => _error;

  Future<void> initialize() async {
    _user = await _repo.restoreSession();
    _initializing = false;
    notifyListeners();
  }

  Future<bool> login({required String email, required String password}) async {
    return _guard(() => _repo.login(email: email, password: password));
  }

  Future<bool> register({
    required String name,
    required String email,
    required String password,
    required String role,
  }) async {
    return _guard(
        () => _repo.register(name: name, email: email, password: password, role: role));
  }

  Future<bool> _guard(Future<UserProfile> Function() action) async {
    _busy = true;
    _error = null;
    notifyListeners();
    try {
      _user = await action();
      return true;
    } catch (e) {
      _error = e.toString();
      return false;
    } finally {
      _busy = false;
      notifyListeners();
    }
  }

  Future<void> logout() async {
    await _repo.logout();
    _user = null;
    notifyListeners();
  }

  CacheService get cache => _cache;
  ApiClient get api => _api;
}
