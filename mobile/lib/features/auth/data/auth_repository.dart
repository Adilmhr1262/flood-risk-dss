import '../../../core/api_client.dart';
import '../../../core/token_storage.dart';

/// Signed-in user profile snapshot.
class UserProfile {
  final String name;
  final String email;
  final String role;

  const UserProfile({required this.name, required this.email, required this.role});

  bool get isAuthority => role == 'authority';
  bool get isNgo => role == 'ngo';
  bool get isVolunteer => role == 'volunteer';
}

/// Authentication repository: register, login, logout, session restore.
class AuthRepository {
  AuthRepository({required ApiClient api, required TokenStorage tokens})
      : _api = api,
        _tokens = tokens;

  final ApiClient _api;
  final TokenStorage _tokens;

  Future<UserProfile> login({required String email, required String password}) async {
    final data = await _api.post('/auth/login', data: {
      'email': email,
      'password': password,
    }) as Map<String, dynamic>;
    return _saveSession(data, email: email);
  }

  Future<UserProfile> register({
    required String name,
    required String email,
    required String password,
    required String role,
  }) async {
    final data = await _api.post('/auth/register', data: {
      'name': name,
      'email': email,
      'password': password,
      'role': role,
    }) as Map<String, dynamic>;
    return _saveSession(data, email: email);
  }

  Future<UserProfile> _saveSession(Map<String, dynamic> data, {required String email}) async {
    final role = (data['role'] as String?) ?? 'public';
    // Fetch the display name from /auth/me so the UI greets the user properly.
    String name = email;
    try {
      final me = await _api.get('/auth/me') as Map<String, dynamic>;
      name = (me['name'] as String?) ?? email;
    } catch (_) {
      // Non-fatal: keep the email as the display name.
    }
    await _tokens.saveSession(
      accessToken: data['access_token'] as String,
      refreshToken: data['refresh_token'] as String,
      role: role,
      name: name,
      email: email,
    );
    return UserProfile(name: name, email: email, role: role);
  }

  Future<UserProfile?> restoreSession() async {
    if (!await _tokens.hasSession()) return null;
    final role = await _tokens.readRole() ?? 'public';
    final name = await _tokens.readName() ?? '';
    final email = await _tokens.readEmail() ?? '';
    return UserProfile(name: name, email: email, role: role);
  }

  Future<void> logout() async {
    try {
      await _api.post('/auth/logout');
    } catch (_) {
      // Logout is stateless; local cleanup happens regardless.
    }
    await _tokens.clear();
  }
}
