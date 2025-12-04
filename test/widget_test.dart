// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:quality_control_app/main.dart';

void main() {
  testWidgets('App smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(
      const QualityControlApp(initialScreen: Scaffold(body: Text('Test'))),
    );

    // Wait for animations and async operations to complete
    await tester.pumpAndSettle();

    // Verify that the app bar title is present.
    // Note: If ApiService fails, it should show 'Нет активных заявок' or just the AppBar.
    expect(find.text('Мои заявки'), findsOneWidget);

    // Verify FAB is present
    expect(find.byIcon(Icons.add), findsOneWidget);
  });
}
