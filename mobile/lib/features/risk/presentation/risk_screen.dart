import 'package:flutter/material.dart';
import 'package:geolocator/geolocator.dart';
import 'package:provider/provider.dart';

import '../../../widgets/common.dart';
import '../../auth/presentation/auth_provider.dart';
import '../data/risk_repository.dart';

/// On-demand risk assessment: pick a district (or use GPS), enter current
/// conditions, and get a machine learning-based prediction with contributing
/// factors and recommendations.
class RiskScreen extends StatefulWidget {
  const RiskScreen({super.key});

  @override
  State<RiskScreen> createState() => _RiskScreenState();
}

class _RiskScreenState extends State<RiskScreen> {
  final _formKey = GlobalKey<FormState>();
  final _rainfall = TextEditingController(text: '120');
  final _temp = TextEditingController(text: '33');
  final _humidity = TextEditingController(text: '80');

  List<Map<String, dynamic>> _districts = [];
  String? _district;
  Map<String, dynamic>? _result;
  bool _loadingDistricts = true;
  bool _assessing = false;
  String? _error;
  bool _locating = false;

  @override
  void initState() {
    super.initState();
    _loadDistricts();
  }

  @override
  void dispose() {
    _rainfall.dispose();
    _temp.dispose();
    _humidity.dispose();
    super.dispose();
  }

  Future<void> _loadDistricts() async {
    try {
      final auth = context.read<AuthProvider>();
      final districts =
          await RiskRepository(api: auth.api, cache: auth.cache).districts();
      if (!mounted) return;
      setState(() {
        _districts = districts;
        if (districts.isNotEmpty) {
          _district = districts.first['district_name'] as String?;
        }
        _loadingDistricts = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loadingDistricts = false;
      });
    }
  }

  Future<void> _useGps() async {
    setState(() => _locating = true);
    try {
      final pos = await Geolocator.getCurrentPosition(
        locationSettings:
            const LocationSettings(timeLimit: Duration(seconds: 8)),
      );
      if (!mounted) return;
      final auth = context.read<AuthProvider>();
      final repo = RiskRepository(api: auth.api, cache: auth.cache);
      final result =
          await repo.myRisk(lat: pos.latitude, lon: pos.longitude);
      if (!mounted) return;
      setState(() {
        _district = result.risk['district_name'] as String?;
        _result = result.risk;
      });
      if (mounted && result.offline) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Offline — showing cached assessment')),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context)
            .showSnackBar(SnackBar(content: Text('GPS failed: $e')));
      }
    } finally {
      if (mounted) setState(() => _locating = false);
    }
  }

  Future<void> _assess() async {
    if (!_formKey.currentState!.validate() || _district == null) return;
    setState(() {
      _assessing = true;
      _error = null;
      _result = null;
    });
    try {
      final auth = context.read<AuthProvider>();
      // District static attributes come from the district list.
      final meta = _districts.firstWhere(
        (d) => d['district_name'] == _district,
        orElse: () => <String, dynamic>{},
      );
      final input = {
        'district_name': _district,
        'rainfall_mm': double.parse(_rainfall.text),
        'temperature_c': double.parse(_temp.text),
        'humidity_pct': double.parse(_humidity.text),
        'elevation_m': (meta['elevation_m'] as num?)?.toDouble() ?? 50.0,
        'river_distance_km': (meta['river_distance_km'] as num?)?.toDouble() ?? 10.0,
        'slope_deg': (meta['slope_deg'] as num?)?.toDouble() ?? 2.0,
        'population_density':
            (meta['population_density_per_km2'] as num?)?.toDouble() ?? 200.0,
        'prev_flood_events': 1,
        'last_severity': 3,
      };
      final result = await RiskRepository(api: auth.api, cache: auth.cache)
          .assess(input);
      if (!mounted) return;
      // Normalize the /risk/predict payload to the card's expected shape.
      setState(() {
        _result = {
          'district_name': result['district_name'] ?? _district,
          'risk_level': result['risk_level'],
          'probability': (result['probability'] as num?) != null
              ? (result['probability'] as num).toDouble() * 100
              : null,
          'main_factors': result['main_factors'],
          'recommendations': result['recommendations'],
          'model_version': result['model_version'],
          'updated_at': DateTime.now().toIso8601String(),
        };
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _assessing = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Risk assessment')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (_loadingDistricts)
              const LoadingView(message: 'Loading districts…')
            else ...[
              Row(
                children: [
                  Expanded(
                    child: DropdownButtonFormField<String>(
                      initialValue: _district,
                      decoration: const InputDecoration(
                        labelText: 'District',
                        border: OutlineInputBorder(),
                      ),
                      items: _districts
                          .map((d) => DropdownMenuItem<String>(
                                value: d['district_name'] as String?,
                                child: Text(
                                    '${d['district_name']} (${d['province'] ?? ''})'),
                              ))
                          .toList(),
                      onChanged: (v) => setState(() => _district = v),
                    ),
                  ),
                  const SizedBox(width: 8),
                  IconButton.filledTonal(
                    tooltip: 'Use my GPS location',
                    onPressed: _locating ? null : _useGps,
                    icon: _locating
                        ? const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.my_location),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Form(
                key: _formKey,
                child: Column(
                  children: [
                    _numberField(_rainfall, 'Rainfall (mm)', Icons.water_drop_outlined),
                    const SizedBox(height: 12),
                    _numberField(_temp, 'Temperature (°C)', Icons.thermostat_outlined),
                    const SizedBox(height: 12),
                    _numberField(_humidity, 'Humidity (%)', Icons.opacity_outlined),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              _assessing
                  ? const LoadingView(message: 'Assessing risk…')
                  : ElevatedButton.icon(
                      onPressed: _assess,
                      icon: const Icon(Icons.assessment),
                      label: const Text('Assess flood risk'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 14),
                      ),
                    ),
            ],
            if (_error != null) ...[
              const SizedBox(height: 12),
              ErrorView(message: _error!, onRetry: _assess),
            ],
            if (_result != null) ...[
              const SizedBox(height: 16),
              _ResultCard(result: _result!),
            ],
          ],
        ),
      ),
    );
  }

  Widget _numberField(
      TextEditingController controller, String label, IconData icon) {
    return TextFormField(
      controller: controller,
      keyboardType: const TextInputType.numberWithOptions(decimal: true),
      decoration: InputDecoration(
        labelText: label,
        prefixIcon: Icon(icon),
        border: const OutlineInputBorder(),
      ),
      validator: (v) =>
          (v == null || double.tryParse(v) == null) ? 'Enter a number' : null,
    );
  }
}

class _ResultCard extends StatelessWidget {
  final Map<String, dynamic> result;
  const _ResultCard({required this.result});

  @override
  Widget build(BuildContext context) {
    final factors = (result['main_factors'] as List?)?.cast<String>() ?? [];
    final recommendations =
        (result['recommendations'] as List?)?.cast<String>() ?? [];
    return Card(
      elevation: 2,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: RiskBadge(
                riskLevel: result['risk_level'] as String? ?? 'UNKNOWN',
                probability: (result['probability'] as num?)?.toDouble(),
              ),
            ),
            const SizedBox(height: 12),
            if (factors.isNotEmpty) ...[
              const Text('Contributing factors',
                  style: TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 4),
              ...factors.map((f) => ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.trending_up, size: 18),
                    title: Text(f, style: const TextStyle(fontSize: 14)),
                  )),
            ],
            if (recommendations.isNotEmpty) ...[
              const Text('Recommendations',
                  style: TextStyle(fontWeight: FontWeight.w600)),
              const SizedBox(height: 4),
              ...recommendations.map((r) => ListTile(
                    dense: true,
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.check_circle_outline,
                        size: 18, color: Colors.green),
                    title: Text(r, style: const TextStyle(fontSize: 14)),
                  )),
            ],
            const SizedBox(height: 8),
            Text(
              'Model: ${result['model_version'] ?? '—'}',
              style: const TextStyle(color: Colors.grey, fontSize: 12),
            ),
          ],
        ),
      ),
    );
  }
}
