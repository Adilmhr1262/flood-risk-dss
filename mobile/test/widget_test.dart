import 'package:flood_risk_dss/features/auth/presentation/auth_provider.dart';
import 'package:flood_risk_dss/features/auth/presentation/login_screen.dart';
import 'package:flood_risk_dss/features/safety/presentation/safety_screen.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:provider/provider.dart';

class _MockAuthProvider extends Mock implements AuthProvider {}

/// Widget tests for key screens (no network; AuthProvider mocked).
void main() {
  testWidgets('login screen shows email/password fields and validates',
      (tester) async {
    final auth = _MockAuthProvider();
    when(() => auth.busy).thenReturn(false);
    when(() => auth.error).thenReturn(null);
    when(() => auth.login(email: any(named: 'email'), password: any(named: 'password')))
        .thenAnswer((_) async => true);

    await tester.pumpWidget(
      ChangeNotifierProvider<AuthProvider>.value(
        value: auth,
        child: const MaterialApp(home: LoginScreen()),
      ),
    );

    expect(find.text('Email'), findsOneWidget);
    expect(find.text('Password'), findsOneWidget);
    expect(find.text('Sign in'), findsWidgets);

    // Empty submit shows validation errors, no login attempt.
    await tester.tap(find.widgetWithText(ElevatedButton, 'Sign in'));
    await tester.pump();
    expect(find.text('Enter a valid email'), findsOneWidget);
    verifyNever(() => auth.login(email: any(named: 'email'), password: any(named: 'password')));
  });

  testWidgets('login submits credentials on valid input', (tester) async {
    final auth = _MockAuthProvider();
    when(() => auth.busy).thenReturn(false);
    when(() => auth.error).thenReturn(null);
    when(() => auth.login(email: any(named: 'email'), password: any(named: 'password')))
        .thenAnswer((_) async => true);

    await tester.pumpWidget(
      ChangeNotifierProvider<AuthProvider>.value(
        value: auth,
        child: const MaterialApp(home: LoginScreen()),
      ),
    );

    await tester.enterText(
        find.widgetWithText(TextFormField, 'Email'), 'vol@example.pk');
    await tester.enterText(
        find.widgetWithText(TextFormField, 'Password'), 'secret123');
    await tester.tap(find.widgetWithText(ElevatedButton, 'Sign in'));
    await tester.pump();
    verify(() => auth.login(email: 'vol@example.pk', password: 'secret123'))
        .called(1);
    // Flush one-shot debounce timers from screens built after navigation
    // (e.g. the map's tile layer) so teardown sees no pending timers.
    await tester.pump(const Duration(seconds: 30));
  });

  testWidgets('safety guide renders bundled offline sections', (tester) async {
    await tester.pumpWidget(const MaterialApp(home: SafetyScreen()));

    expect(find.text('Safety guide'), findsOneWidget);
    expect(find.text('Before the monsoon'), findsOneWidget);
    expect(find.text('When flood water rises'), findsOneWidget);
    expect(find.text('Emergency kit checklist'), findsOneWidget);

    // Expanding a section reveals its points.
    await tester.tap(find.text('Before the monsoon'));
    await tester.pumpAndSettle();
    expect(find.textContaining('emergency kit'), findsWidgets);
  });
}
