/// App-wide configuration.
///
/// The API base URL can be overridden at build/run time:
/// `flutter run --dart-define=API_BASE_URL=http://192.168.1.5:8000/api/v1`
/// Defaults to the Android emulator loopback address.
class AppConfig {
  static const String apiBaseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000/api/v1',
  );

  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 20);

  /// How long cached offline data is considered fresh.
  static const Duration cacheTtl = Duration(hours: 6);
}
