import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../../widgets/common.dart';
import '../../auth/presentation/auth_provider.dart';
import '../data/alerts_repository.dart';

/// Warning notifications and risk-change alerts for the community.
class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  List<Map<String, dynamic>> _alerts = [];
  bool _offline = false;
  bool _loading = true;
  String? _error;

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
      final result = await AlertsRepository(api: auth.api, cache: auth.cache)
          .activeAlerts();
      if (!mounted) return;
      setState(() {
        _alerts = result.alerts;
        _offline = result.offline;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Color _severityColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'critical':
        return Colors.red.shade800;
      case 'warning':
        return Colors.orange.shade800;
      case 'info':
        return Colors.blue.shade800;
      default:
        return Colors.grey.shade700;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Alerts & warnings')),
      body: RefreshIndicator(
        onRefresh: _load,
        child: _loading
            ? const LoadingView(message: 'Loading alerts…')
            : _error != null
                ? ErrorView(message: _error!, onRetry: _load)
                : Column(
                    children: [
                      if (_offline) const OfflineBanner(),
                      Expanded(
                        child: _alerts.isEmpty
                            ? const EmptyView(
                                message:
                                    'No active alerts. You will be notified here when a warning is issued.',
                                icon: Icons.notifications_none,
                              )
                            : ListView.separated(
                                padding: const EdgeInsets.all(12),
                                itemCount: _alerts.length,
                                separatorBuilder: (_, __) =>
                                    const SizedBox(height: 8),
                                itemBuilder: (ctx, i) {
                                  final a = _alerts[i];
                                  final severity =
                                      (a['severity'] as String?) ?? 'info';
                                  return Card(
                                    child: ListTile(
                                      leading: CircleAvatar(
                                        backgroundColor: _severityColor(severity)
                                            .withValues(alpha: 0.15),
                                        child: Icon(
                                          Icons.warning_amber_rounded,
                                          color: _severityColor(severity),
                                        ),
                                      ),
                                      title: Text(
                                        a['title'] as String? ?? 'Alert',
                                        style: const TextStyle(
                                            fontWeight: FontWeight.w600),
                                      ),
                                      subtitle: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          const SizedBox(height: 4),
                                          Text(a['message'] as String? ?? ''),
                                          const SizedBox(height: 4),
                                          Text(
                                            '${a['district_name'] ?? 'All districts'} · ${_formatTime(a['issued_at'] as String?)}',
                                            style: const TextStyle(
                                                fontSize: 12, color: Colors.grey),
                                          ),
                                        ],
                                      ),
                                      trailing: Chip(
                                        label: Text(
                                          severity.toUpperCase(),
                                          style: const TextStyle(fontSize: 10),
                                        ),
                                        backgroundColor:
                                            _severityColor(severity).withValues(alpha: 0.15),
                                      ),
                                    ),
                                  );
                                },
                              ),
                      ),
                    ],
                  ),
      ),
    );
  }

  String _formatTime(String? iso) {
    if (iso == null) return '';
    try {
      final dt = DateTime.parse(iso).toLocal();
      return '${dt.day}/${dt.month}/${dt.year} ${dt.hour}:${dt.minute.toString().padLeft(2, '0')}';
    } catch (_) {
      return iso;
    }
  }
}
