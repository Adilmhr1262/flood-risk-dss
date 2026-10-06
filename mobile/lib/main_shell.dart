import 'package:flutter/material.dart';

import 'features/alerts/presentation/alerts_screen.dart';
import 'features/emergency/presentation/emergency_screen.dart';
import 'features/home/presentation/home_screen.dart';
import 'features/map/presentation/map_screen.dart';
import 'features/risk/presentation/risk_screen.dart';
import 'features/safety/presentation/safety_screen.dart';

/// Main tab shell after sign-in: Home, Risk, Map, Alerts, Emergency.
class MainShell extends StatefulWidget {
  const MainShell({super.key});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _index = 0;

  static const _screens = [
    HomeScreen(),
    RiskScreen(),
    MapScreen(),
    AlertsScreen(),
    EmergencyScreen(),
  ];

  void _goTo(int index) => setState(() => _index = index);

  @override
  Widget build(BuildContext context) {
    return TabNavigator(
      goTo: _goTo,
      child: Scaffold(
        body: IndexedStack(index: _index, children: _screens),
        bottomNavigationBar: NavigationBar(
          selectedIndex: _index,
          onDestinationSelected: _goTo,
          destinations: const [
            NavigationDestination(
                icon: Icon(Icons.home_outlined),
                selectedIcon: Icon(Icons.home),
                label: 'Home'),
            NavigationDestination(
                icon: Icon(Icons.assessment_outlined),
                selectedIcon: Icon(Icons.assessment),
                label: 'Risk'),
            NavigationDestination(
                icon: Icon(Icons.map_outlined),
                selectedIcon: Icon(Icons.map),
                label: 'Map'),
            NavigationDestination(
                icon: Icon(Icons.notifications_outlined),
                selectedIcon: Icon(Icons.notifications),
                label: 'Alerts'),
            NavigationDestination(
                icon: Icon(Icons.sos_outlined),
                selectedIcon: Icon(Icons.sos),
                label: 'Emergency'),
          ],
        ),
        floatingActionButton: _index == 0
            ? FloatingActionButton.extended(
                onPressed: () => Navigator.of(context).push(
                  MaterialPageRoute(builder: (_) => const SafetyScreen()),
                ),
                icon: const Icon(Icons.menu_book_outlined),
                label: const Text('Safety guide'),
              )
            : null,
      ),
    );
  }
}
