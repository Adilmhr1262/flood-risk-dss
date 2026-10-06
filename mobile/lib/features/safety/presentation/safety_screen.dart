import 'package:flutter/material.dart';

import '../data/safety_content.dart';

/// Offline disaster-preparedness guide. All content is bundled with the app
/// so it works with no network connection.
class SafetyScreen extends StatelessWidget {
  const SafetyScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Safety guide')),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          const Card(
            color: Color(0xFFE3F2FD),
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Row(
                children: [
                  Icon(Icons.offline_bolt, color: Colors.blue, size: 32),
                  SizedBox(width: 12),
                  Expanded(
                    child: Text(
                      'This guide is stored on your phone and works offline. Read it before the monsoon season.',
                      style: TextStyle(fontSize: 13),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 8),
          ...safetyGuide.map((section) => Card(
                margin: const EdgeInsets.only(bottom: 8),
                child: ExpansionTile(
                  leading: Text(section.icon,
                      style: const TextStyle(fontSize: 26)),
                  title: Text(section.title,
                      style: const TextStyle(fontWeight: FontWeight.w600)),
                  children: section.points
                      .map(
                        (p) => ListTile(
                          dense: true,
                          leading: const Icon(Icons.check_circle_outline,
                              size: 18, color: Colors.green),
                          title: Text(p, style: const TextStyle(fontSize: 14)),
                        ),
                      )
                      .toList(),
                ),
              )),
        ],
      ),
    );
  }
}
