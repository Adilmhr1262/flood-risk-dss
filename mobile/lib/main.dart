import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/api_client.dart';
import 'core/cache_service.dart';
import 'core/token_storage.dart';
import 'features/auth/presentation/auth_provider.dart';
import 'features/auth/presentation/splash_screen.dart';

void main() {
  runApp(const FloodRiskApp());
}

class FloodRiskApp extends StatelessWidget {
  const FloodRiskApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider(
          create: (_) => AuthProvider(
            api: ApiClient(),
            tokens: TokenStorage(),
            cache: CacheService(),
          ),
        ),
      ],
      child: MaterialApp(
        title: 'Flood Risk DSS',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
          useMaterial3: true,
        ),
        home: const SplashScreen(),
      ),
    );
  }
}
