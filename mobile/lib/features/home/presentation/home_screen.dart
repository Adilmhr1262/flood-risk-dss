import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:provider/provider.dart';

import '../../../core/app_error.dart';
import '../../../widgets/common.dart';
import '../../auth/presentation/auth_provider.dart';
import '../../risk/data/risk_repository.dart';

/// Home dashboard: current location, risk level, probability, last update.
class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  Map<String, dynamic>? _risk;
  bool _offline = false;
  bool _loading = true;
  String? _error;
  String? _locationLabel;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final auth = context.read<AuthProvider>();
      final repo = RiskRepository(api: auth.api, cache: auth.cache);

      // Try GPS first; fall back to the district list's first entry via cache.
      String? district;
      double? lat, lon;
      try {
        final permission = await Geolocator.checkPermission();
        if (permission == LocationPermission.denied) {
          await Geolocator.requestPermission();
        }
        final pos = await Geolocator.getCurrentPosition(
          locationSettings:
              const LocationSettings(timeLimit: Duration(seconds: 8)),
        );
        lat = pos.latitude;
        lon = pos.longitude;
        _locationLabel =
            '${lat.toStringAsFixed(2)}, ${lon.toStringAsFixed(2)}';
      } catch (_) {
        _locationLabel = 'GPS unavailable';
      }

      final result = await repo.myRisk(districtName: district, lat: lat, lon: lon);
      if (!mounted) return;
      setState(() {
        _risk = result.risk;
        _offline = result.offline;
        _locationLabel = result.risk['district_name'] as String? ?? _locationLabel;
      });
    } on NotFoundException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.message);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final user = auth.user;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Flood Risk DSS'),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sign out',
            onPressed: () async {
              await auth.logout();
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (_offline) const OfflineBanner(),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Row(
                  children: [
                    const CircleAvatar(
                      radius: 24,
                      child: Icon(Icons.person, size: 28),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            'Assalam-o-Alaikum, ${user?.name ?? ''}',
                            style: const TextStyle(
                                fontSize: 16, fontWeight: FontWeight.w600),
                          ),
                          Text(
                            '${user?.role.toUpperCase() ?? ''} · ${_locationLabel ?? 'Locating…'}',
                            style: const TextStyle(color: Colors.grey, fontSize: 12),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 12),
            if (_loading)
              const SizedBox(height: 200, child: LoadingView(message: 'Checking flood risk…'))
            else if (_error != null)
              SizedBox(
                height: 200,
                child: ErrorView(message: _error!, onRetry: _load),
              )
            else if (_risk != null)
              _RiskCard(risk: _risk!),
            const SizedBox(height: 12),
            _QuickActions(),
          ],
        ),
      ),
    );
  }
}

class _RiskCard extends StatelessWidget {
  final Map<String, dynamic> risk;
  const _RiskCard({required this.risk});

  @override
  Widget build(BuildContext context) {
    final factors = (risk['main_factors'] as List?)?.cast<String>() ?? [];
    final recommendations =
        (risk['recommendations'] as List?)?.cast<String>() ?? [];
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    risk['district_name'] as String? ?? 'Unknown district',
                    style: const TextStyle(
                        fontSize: 18, fontWeight: FontWeight.bold),
                  ),
                ),
                RiskBadge(
                  riskLevel: risk['risk_level'] as String? ?? 'UNKNOWN',
                  probability: (risk['probability'] as num?)?.toDouble(),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Text(
              'Last update: ${_formatTime(risk['updated_at'] as String?)}',
              style: const TextStyle(color: Colors.grey, fontSize: 12),
            ),
            Text(
              'Model: ${risk['model_version'] ?? '—'}',
              style: const TextStyle(color: Colors.grey, fontSize: 12),
            ),
            if (factors.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text('Why this risk?',
                  style: TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 4),
              ...factors.take(4).map(
                    (f) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Row(
                        children: [
                          const Icon(Icons.fiber_manual_record,
                              size: 8, color: Colors.blueGrey),
                          const SizedBox(width: 8),
                          Expanded(child: Text(f)),
                        ],
                      ),
                    ),
                  ),
            ],
            if (recommendations.isNotEmpty) ...[
              const SizedBox(height: 12),
              const Text('What to do',
                  style: TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 4),
              ...recommendations.take(3).map(
                    (r) => Padding(
                      padding: const EdgeInsets.symmetric(vertical: 2),
                      child: Row(
                        children: [
                          const Icon(Icons.check_circle_outline,
                              size: 16, color: Colors.green),
                          const SizedBox(width: 8),
                          Expanded(child: Text(r)),
                        ],
                      ),
                    ),
                  ),
            ],
          ],
        ),
      ),
    );
  }

  String _formatTime(String? iso) {
    if (iso == null) return 'unknown';
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day}/${dt.month}/${dt.year} ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return iso;
    }
  }
}

class _QuickActions extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      mainAxisSpacing: 8,
      crossAxisSpacing: 8,
      childAspectRatio: 1.6,
      children: [
        _ActionTile(
          icon: Icons.assessment_outlined,
          label: 'Risk assessment',
          onTap: () => _goToTab(context, 1),
        ),
        _ActionTile(
          icon: Icons.map_outlined,
          label: 'Risk map',
          onTap: () => _goToTab(context, 2),
        ),
        _ActionTile(
          icon: Icons.notifications_outlined,
          label: 'Alerts',
          onTap: () => _goToTab(context, 3),
        ),
        _ActionTile(
          icon: Icons.sos_outlined,
          label: 'Emergency',
          onTap: () => _goToTab(context, 4),
        ),
      ],
    );
  }

  void _goToTab(BuildContext context, int index) {
    // MainShell exposes a tab controller via an inherited notifier.
    TabNavigator.of(context)?.goTo(index);
  }
}

/// Simple inherited widget so home quick-actions can switch bottom-nav tabs.
class TabNavigator extends InheritedWidget {
  final void Function(int) goTo;
  const TabNavigator({super.key, required this.goTo, required super.child});

  static TabNavigator? of(BuildContext context) =>
      context.dependOnInheritedWidgetOfExactType<TabNavigator>();

  @override
  bool updateShouldNotify(TabNavigator oldWidget) => goTo != oldWidget.goTo;
}

class _ActionTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final VoidCallback onTap;
  const _ActionTile(
      {required this.icon, required this.label, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 32, color: Theme.of(context).colorScheme.primary),
            const SizedBox(height: 8),
            Text(label, style: const TextStyle(fontWeight: FontWeight.w500)),
          ],
        ),
      ),
    );
  }
}
