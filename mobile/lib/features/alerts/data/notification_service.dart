import '../../../core/api_client.dart';
import '../../../core/app_error.dart';

/// Push-notification token registration for the early-warning system.
///
/// The app obtains an FCM token through the `firebase_messaging` plugin
/// (native Firebase setup is a production integration step — see
/// docs/early-warning-system.md) and registers it here so the backend can
/// push flood advisories and emergency warnings to this device.
///
/// Production wiring (not bundled in this repo):
///   1. Add `firebase_messaging: ^15.0.0` to pubspec.yaml.
///   2. Add google-services.json (Android) / GoogleService-Info.plist (iOS)
///      and the Gradle / Xcode plugin configuration.
///   3. Request notification permission, then:
///        final token = await FirebaseMessaging.instance.getToken();
///        await NotificationService(api).registerToken(token!, platform: 'android');
class NotificationService {
  NotificationService({required ApiClient api}) : _api = api;

  final ApiClient _api;

  /// Register (or refresh) this device's FCM token for push warnings.
  Future<void> registerToken(String fcmToken, {String platform = 'android'}) async {
    try {
      await _api.post('/mobile/device-token', data: {
        'fcm_token': fcmToken,
        'platform': platform,
      });
    } on NetworkException {
      // Registration is best-effort: the user still gets alerts through the
      // in-app inbox when connectivity returns.
    }
  }

  /// Remove this device's FCM token (logout / opt-out of push warnings).
  Future<void> unregisterToken(String fcmToken) async {
    try {
      await _api.delete('/mobile/device-token', query: {'fcm_token': fcmToken});
    } on NetworkException {
      // Best-effort; the token stays registered until the next successful call.
    }
  }
}
