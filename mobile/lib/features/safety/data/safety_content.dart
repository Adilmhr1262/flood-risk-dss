/// Bundled offline flood-preparedness content for the Safety Guide screen.
/// Always available, even with no network connection.
library;

class SafetySection {
  final String title;
  final String icon;
  final List<String> points;

  const SafetySection({required this.title, required this.icon, required this.points});
}

const List<SafetySection> safetyGuide = [
  SafetySection(
    title: 'Before the monsoon',
    icon: '☔',
    points: [
      'Know your district risk: check this app\'s risk assessment before July each year.',
      'Prepare an emergency kit: drinking water (3 days), dry food, torch, batteries, first-aid box, important documents in a waterproof bag.',
      'Keep CNICs, land papers and children\'s B-forms in a sealed plastic pouch, stored high.',
      'Identify the nearest shelter or high ground and plan two routes to reach it.',
      'Charge mobile phones and keep a power bank ready; save Rescue 1122 and PDMA helpline numbers.',
      'Move livestock to raised ground early; tie boats and secure loose items around the house.',
      'If you live near a river or embankment, agree on a family meeting point in case you are separated.',
    ],
  ),
  SafetySection(
    title: 'When flood water rises',
    icon: '🌊',
    points: [
      'Move to high ground immediately — do not wait for an official order if water is entering your street.',
      'Never walk through flowing water above ankle depth; 15 cm of fast water can knock you down.',
      'Never drive through flooded roads — most flood deaths in Pakistan happen in vehicles.',
      'Turn off electricity and gas at the mains before leaving the house.',
      'Do not drink flood water; use bottled or boiled water to avoid cholera and diarrhoea.',
      'Keep children and elderly close; carry infants and help neighbours who cannot move alone.',
      'Listen to radio/TV and this app\'s alerts for evacuation orders and shelter locations.',
    ],
  ),
  SafetySection(
    title: 'After the flood',
    icon: '🏠',
    points: [
      'Return home only after authorities declare the area safe.',
      'Check walls, roofs and electric wiring for damage before switching power on.',
      'Throw away food that touched flood water; disinfect utensils and water containers.',
      'Watch for snakes and insects displaced by water; wear boots and gloves while cleaning.',
      'Report damaged embankments, blocked drains or broken hand pumps to the district administration.',
      'Seek medical help for fever, diarrhoea or skin infections — free camps are usually set up after major floods.',
    ],
  ),
  SafetySection(
    title: 'Emergency kit checklist',
    icon: '🎒',
    points: [
      'Drinking water — 4 litres per person per day for 3 days',
      'Dry food: dates, biscuits, roasted gram, powdered milk',
      'Torch + extra batteries, candles and matchbox in a sealed bag',
      'First-aid box, ORS packets, prescribed medicines',
      'CNIC copies, cash in small notes, mobile charger / power bank',
      'Rope, plastic sheets, mosquito net, spare clothes',
      'Whistle — to signal rescuers if trapped',
    ],
  ),
  SafetySection(
    title: 'Important numbers (Sindh)',
    icon: '📞',
    points: [
      'Rescue 1122 — provincial emergency helpline (24/7)',
      'PDMA Sindh control room — check this app\'s emergency contacts for the current number',
      'Police — 15',
      'Edhi ambulance — 115',
      'Keep your district administration\'s flood control room number saved before the monsoon',
    ],
  ),
];
