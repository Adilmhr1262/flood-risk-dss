import 'package:flutter/material.dart';
import 'package:flutter_map/flutter_map.dart';
import 'package:latlong2/latlong.dart';
import 'package:provider/provider.dart';

import '../../../core/app_error.dart';
import '../../../widgets/common.dart';
import '../../auth/presentation/auth_provider.dart';

/// Interactive GIS map: risk zones, shelters and critical infrastructure
/// rendered from the backend GeoJSON layers, with layer toggles.
class _Layer {
  final String key;
  final String label;
  final IconData icon;
  final Color color;
  bool visible = true;
  List<Marker> markers = [];

  _Layer({
    required this.key,
    required this.label,
    required this.icon,
    required this.color,
  });
}

class MapScreen extends StatefulWidget {
  const MapScreen({super.key});

  @override
  State<MapScreen> createState() => _MapScreenState();
}

class _MapScreenState extends State<MapScreen> {
  final MapController _mapController = MapController();
  late final List<_Layer> _layers;
  bool _loading = true;
  String? _error;

  static const _riskColors = {
    'HIGH': Colors.red,
    'MEDIUM': Colors.orange,
    'LOW': Colors.green,
  };

  @override
  void initState() {
    super.initState();
    _layers = [
      _Layer(key: 'risk', label: 'Risk zones', icon: Icons.warning, color: Colors.red),
      _Layer(key: 'shelters', label: 'Shelters', icon: Icons.home, color: Colors.blue),
      _Layer(
          key: 'infrastructure',
          label: 'Hospitals & rescue',
          icon: Icons.local_hospital,
          color: Colors.purple),
    ];
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final api = context.read<AuthProvider>().api;
      final results = await Future.wait([
        api.get('/gis/risk-layer'),
        api.get('/gis/shelters'),
        api.get('/gis/infrastructure'),
      ]);
      if (!mounted) return;
      _layers[0].markers = _riskMarkers(results[0] as Map<String, dynamic>);
      _layers[1].markers = _pointMarkers(
        results[1] as Map<String, dynamic>,
        Colors.blue,
        Icons.home,
        (p) => "${p['name']}\nCapacity: ${p['capacity'] ?? '—'}",
      );
      _layers[2].markers = _pointMarkers(
        results[2] as Map<String, dynamic>,
        Colors.purple,
        Icons.local_hospital,
        (p) => "${p['name']}\n${p['type']}",
      );
      // Fit the map to the risk points.
      final pts = _layers[0].markers.map((m) => m.point).toList();
      if (pts.isNotEmpty) {
        final bounds = LatLngBounds.fromPoints(pts);
        _mapController.fitCamera(CameraFit.bounds(bounds: bounds, padding: const EdgeInsets.all(40)));
      }
    } on NetworkException catch (e) {
      if (!mounted) return;
      setState(() => _error = e.message);
    } catch (e) {
      if (!mounted) return;
      setState(() => _error = e.toString());
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<Marker> _riskMarkers(Map<String, dynamic> collection) {
    final markers = <Marker>[];
    for (final f in (collection['features'] as List).cast<Map<String, dynamic>>()) {
      final coords = (f['geometry'] as Map)['coordinates'] as List;
      final props = (f['properties'] as Map).cast<String, dynamic>();
      final level = (props['risk_level'] as String?) ?? 'UNKNOWN';
      final color = _riskColors[level] ?? Colors.grey;
      markers.add(
        Marker(
          point: LatLng((coords[1] as num).toDouble(), (coords[0] as num).toDouble()),
          width: 44,
          height: 44,
          child: GestureDetector(
            onTap: () => _showInfo(
              props['district_name'] as String? ?? 'District',
              'Risk: $level\nProbability: ${props['probability'] ?? '—'}%',
            ),
            child: Icon(Icons.location_on, color: color, size: 40),
          ),
        ),
      );
    }
    return markers;
  }

  List<Marker> _pointMarkers(
    Map<String, dynamic> collection,
    Color color,
    IconData icon,
    String Function(Map<String, dynamic>) label,
  ) {
    final markers = <Marker>[];
    for (final f in (collection['features'] as List).cast<Map<String, dynamic>>()) {
      final coords = (f['geometry'] as Map)['coordinates'] as List;
      if ((coords[0] as num).toDouble() == 0 && (coords[1] as num).toDouble() == 0) {
        continue;
      }
      final props = (f['properties'] as Map).cast<String, dynamic>();
      markers.add(
        Marker(
          point: LatLng((coords[1] as num).toDouble(), (coords[0] as num).toDouble()),
          width: 36,
          height: 36,
          child: GestureDetector(
            onTap: () => _showInfo(
              props['district_name'] as String? ?? 'Facility',
              label(props),
            ),
            child: Icon(icon, color: color, size: 30),
          ),
        ),
      );
    }
    return markers;
  }

  void _showInfo(String title, String body) {
    showModalBottomSheet(
      context: context,
      builder: (_) => Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
            const SizedBox(height: 8),
            Text(body),
            const SizedBox(height: 12),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Risk map'),
        actions: [
          IconButton(icon: const Icon(Icons.layers), onPressed: _showLayerSheet),
          IconButton(icon: const Icon(Icons.refresh), onPressed: _load),
        ],
      ),
      body: _loading
          ? const LoadingView(message: 'Loading map layers…')
          : _error != null
              ? ErrorView(message: _error!, onRetry: _load)
              : Stack(
                  children: [
                    FlutterMap(
                      mapController: _mapController,
                      options: const MapOptions(
                        initialCenter: LatLng(26.8, 68.0),
                        initialZoom: 7,
                      ),
                      children: [
                        TileLayer(
                          urlTemplate: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
                          userAgentPackageName: 'pk.flooddss.flood_risk_dss',
                        ),
                        for (final layer in _layers)
                          if (layer.visible) MarkerLayer(markers: layer.markers),
                      ],
                    ),
                    Positioned(
                      right: 12,
                      bottom: 12,
                      child: Card(
                        child: Padding(
                          padding: const EdgeInsets.all(8),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            mainAxisSize: MainAxisSize.min,
                            children: const [
                              _LegendDot(color: Colors.red, label: 'High risk'),
                              _LegendDot(color: Colors.orange, label: 'Medium risk'),
                              _LegendDot(color: Colors.green, label: 'Low risk'),
                              _LegendDot(color: Colors.blue, label: 'Shelter'),
                              _LegendDot(color: Colors.purple, label: 'Hospital / rescue'),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
    );
  }

  void _showLayerSheet() {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setSheetState) => Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Map layers',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold)),
              ..._layers.map(
                (l) => SwitchListTile(
                  title: Text(l.label),
                  secondary: Icon(l.icon, color: l.color),
                  value: l.visible,
                  onChanged: (v) {
                    setSheetState(() => l.visible = v);
                    setState(() {});
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _LegendDot extends StatelessWidget {
  final Color color;
  final String label;
  const _LegendDot({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 12,
            height: 12,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 6),
          Text(label, style: const TextStyle(fontSize: 12)),
        ],
      ),
    );
  }
}
