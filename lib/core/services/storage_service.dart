import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

class StorageService {
  static const String _historyKey = 'report_history';

  // Mock database of equipment
  static const List<String> equipmentList = [
    'CNC-101 (Фрезерный станок)',
    'CNC-102 (Токарный станок)',
    'DRILL-201 (Сверлильный станок)',
    'PRESS-301 (Гидравлический пресс)',
    'SAW-401 (Ленточная пила)',
    'WELD-501 (Сварочный аппарат)',
    'CONV-601 (Конвейерная лента)',
    'PUMP-701 (Насосная станция)',
    'GEN-801 (Генератор)',
    'COMP-901 (Компрессор)',
  ];

  Future<void> saveReport(Map<String, String> report) async {
    final prefs = await SharedPreferences.getInstance();
    final List<String> history = prefs.getStringList(_historyKey) ?? [];

    // Add timestamp
    report['timestamp'] = DateTime.now().toIso8601String();

    history.insert(0, jsonEncode(report)); // Add to beginning
    await prefs.setStringList(_historyKey, history);
  }

  Future<List<Map<String, dynamic>>> getHistory() async {
    final prefs = await SharedPreferences.getInstance();
    final List<String> history = prefs.getStringList(_historyKey) ?? [];

    return history.map((e) => jsonDecode(e) as Map<String, dynamic>).toList();
  }

  Future<void> clearHistory() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_historyKey);
  }
}
