import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:provider/provider.dart';
import 'package:url_launcher/url_launcher.dart';

import '../../../widgets/common.dart';
import '../../auth/presentation/auth_provider.dart';
import '../data/emergency_repository.dart';

/// Emergency section: rescue contacts, nearby shelters, hospitals and a
/// flood-sighting report form for volunteers and the public.
class EmergencyScreen extends StatefulWidget {
  const EmergencyScreen({super.key});

  @override
  State<EmergencyScreen> createState() => _EmergencyScreenState();
}

class _EmergencyScreenState extends State<EmergencyScreen>
    with SingleTickerProviderStateMixin {
  late final TabController _tabs = TabController(length: 3, vsync: this);

  @override
  void dispose() {
    _tabs.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Emergency'),
        bottom: TabBar(
          controller: _tabs,
          tabs: const [
            Tab(icon: Icon(Icons.home), text: 'Shelters'),
            Tab(icon: Icon(Icons.phone), text: 'Contacts'),
            Tab(icon: Icon(Icons.report), text: 'Report'),
          ],
        ),
      ),
      body: TabBarView(
        controller: _tabs,
        children: const [
          _SheltersTab(),
          _ContactsTab(),
          _ReportTab(),
        ],
      ),
    );
  }
}

class _SheltersTab extends StatefulWidget {
  const _SheltersTab();

  @override
  State<_SheltersTab> createState() => _SheltersTabState();
}

class _SheltersTabState extends State<_SheltersTab> {
  List<Map<String, dynamic>> _shelters = [];
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
      double lat = 26.73, lon = 67.78; // Sindh fallback
      try {
        final pos = await Geolocator.getCurrentPosition(
          locationSettings:
              const LocationSettings(timeLimit: Duration(seconds: 8)),
        );
        lat = pos.latitude;
        lon = pos.longitude;
      } catch (_) {}
      final result = await EmergencyRepository(api: auth.api, cache: auth.cache)
          .nearbyShelters(lat, lon);
      if (!mounted) return;
      setState(() {
        _shelters = result.shelters;
        _offline = result.offline;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const LoadingView(message: 'Finding nearby shelters…');
    if (_error != null) return ErrorView(message: _error!, onRetry: _load);
    return Column(
      children: [
        if (_offline) const OfflineBanner(),
        Expanded(
          child: _shelters.isEmpty
              ? const EmptyView(
                  message: 'No shelters found within 50 km.',
                  icon: Icons.home_outlined,
                )
              : ListView.separated(
                  padding: const EdgeInsets.all(12),
                  itemCount: _shelters.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (ctx, i) {
                    final s = _shelters[i];
                    final facilities =
                        (s['facilities'] as List?)?.cast<String>() ?? [];
                    return Card(
                      child: ListTile(
                        leading: const CircleAvatar(child: Icon(Icons.home)),
                        title: Text(s['name'] as String? ?? 'Shelter',
                            style:
                                const TextStyle(fontWeight: FontWeight.w600)),
                        subtitle: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                                '${s['distance_km'] ?? '—'} km away · Capacity: ${s['capacity'] ?? '—'}'),
                            if (facilities.isNotEmpty)
                              Text(facilities.join(' · '),
                                  style: const TextStyle(fontSize: 12)),
                          ],
                        ),
                        trailing: s['contact_phone'] != null
                            ? IconButton(
                                icon: const Icon(Icons.call,
                                    color: Colors.green),
                                onPressed: () => _call(s['contact_phone'] as String),
                              )
                            : null,
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }

  Future<void> _call(String phone) async {
    final uri = Uri(scheme: 'tel', path: phone);
    if (await canLaunchUrl(uri)) {
      await launchUrl(uri);
    }
  }
}

class _ContactsTab extends StatefulWidget {
  const _ContactsTab();

  @override
  State<_ContactsTab> createState() => _ContactsTabState();
}

class _ContactsTabState extends State<_ContactsTab> {
  List<Map<String, dynamic>> _contacts = [];
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
      final result = await EmergencyRepository(api: auth.api, cache: auth.cache)
          .contacts();
      if (!mounted) return;
      setState(() {
        _contacts = result.contacts;
        _offline = result.offline;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const LoadingView(message: 'Loading contacts…');
    if (_error != null) return ErrorView(message: _error!, onRetry: _load);
    return Column(
      children: [
        if (_offline) const OfflineBanner(),
        // Always-visible national helplines, available even offline.
        const Padding(
          padding: EdgeInsets.fromLTRB(12, 12, 12, 4),
          child: Card(
            color: Color(0xFFFCE4EC),
            child: ListTile(
              leading: Icon(Icons.sos, color: Colors.red),
              title: Text('Rescue 1122 (Sindh)',
                  style: TextStyle(fontWeight: FontWeight.bold)),
              subtitle: Text('Provincial emergency helpline — 24/7'),
              trailing: _CallButton(phone: '1122'),
            ),
          ),
        ),
        Expanded(
          child: _contacts.isEmpty
              ? const EmptyView(message: 'No contacts cached yet.')
              : ListView.separated(
                  padding: const EdgeInsets.all(12),
                  itemCount: _contacts.length,
                  separatorBuilder: (_, __) => const SizedBox(height: 8),
                  itemBuilder: (ctx, i) {
                    final c = _contacts[i];
                    return Card(
                      child: ListTile(
                        leading: const CircleAvatar(
                            child: Icon(Icons.support_agent)),
                        title: Text(c['name'] as String? ?? ''),
                        subtitle: Text(
                            '${c['organization'] ?? ''} · ${c['district_name'] ?? ''}'),
                        trailing: _CallButton(phone: c['phone'] as String? ?? ''),
                      ),
                    );
                  },
                ),
        ),
      ],
    );
  }
}

class _CallButton extends StatelessWidget {
  final String phone;
  const _CallButton({required this.phone});

  @override
  Widget build(BuildContext context) {
    return IconButton(
      icon: const Icon(Icons.call, color: Colors.green),
      tooltip: 'Call $phone',
      onPressed: () async {
        final uri = Uri(scheme: 'tel', path: phone);
        if (await canLaunchUrl(uri)) {
          await launchUrl(uri);
        } else if (context.mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Cannot place calls on this device: $phone')),
          );
        }
      },
    );
  }
}

class _ReportTab extends StatefulWidget {
  const _ReportTab();

  @override
  State<_ReportTab> createState() => _ReportTabState();
}

const _severityLabels = {
  1: 'Minor — street waterlogging',
  2: 'Moderate — houses affected',
  3: 'Severe — roads cut off',
  4: 'Very severe — evacuations needed',
  5: 'Catastrophic — life-threatening',
};

class _ReportTabState extends State<_ReportTab> {
  final _formKey = GlobalKey<FormState>();
  final _district = TextEditingController();
  final _description = TextEditingController();
  int _severity = 3;
  bool _busy = false;

  @override
  void dispose() {
    _district.dispose();
    _description.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _busy = true);
    try {
      double lat = 26.73, lon = 67.78;
      try {
        final pos = await Geolocator.getCurrentPosition(
          locationSettings:
              const LocationSettings(timeLimit: Duration(seconds: 8)),
        );
        lat = pos.latitude;
        lon = pos.longitude;
      } catch (_) {}
      if (!mounted) return;
      final auth = context.read<AuthProvider>();
      await EmergencyRepository(api: auth.api, cache: auth.cache).reportEvent(
        districtName: _district.text.trim(),
        lat: lat,
        lon: lon,
        severity: _severity,
        description: _description.text.trim(),
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
            content: Text('Report submitted. Thank you for helping your community.')),
      );
      _district.clear();
      _description.clear();
      setState(() => _severity = 3);
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('Report failed: $e')));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Form(
        key: _formKey,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            const Text(
              'Report flooding in your area',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 4),
            const Text(
              'Your report helps authorities verify conditions on the ground. Your GPS location is attached automatically.',
              style: TextStyle(color: Colors.grey, fontSize: 13),
            ),
            const SizedBox(height: 16),
            TextFormField(
              controller: _district,
              decoration: const InputDecoration(
                labelText: 'District',
                prefixIcon: Icon(Icons.location_on_outlined),
                border: OutlineInputBorder(),
              ),
              validator: (v) =>
                  (v == null || v.trim().isEmpty) ? 'Required' : null,
            ),
            const SizedBox(height: 16),
            const Text('Observed severity',
                style: TextStyle(fontWeight: FontWeight.w600)),
            RadioGroup<int>(
              groupValue: _severity,
              onChanged: (v) => setState(() => _severity = v!),
              child: Column(
                children: _severityLabels.entries
                    .map(
                      (e) => RadioListTile<int>(
                        title: Text(e.value),
                        value: e.key,
                      ),
                    )
                    .toList(),
              ),
            ),
            const SizedBox(height: 8),
            TextFormField(
              controller: _description,
              maxLines: 3,
              decoration: const InputDecoration(
                labelText: 'Description (optional)',
                hintText: 'e.g. Water 2 feet deep on Main Road, houses flooded',
                border: OutlineInputBorder(),
              ),
            ),
            const SizedBox(height: 16),
            _busy
                ? const LoadingView(message: 'Submitting report…')
                : ElevatedButton.icon(
                    onPressed: _submit,
                    icon: const Icon(Icons.send),
                    label: const Text('Submit report'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                    ),
                  ),
          ],
        ),
      ),
    );
  }
}
