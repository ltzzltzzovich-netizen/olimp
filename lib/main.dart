import 'package:flutter/material.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'core/constants/app_constants.dart';
import 'core/theme/app_theme.dart';
import 'features/auth/login_screen.dart';
import 'features/home/home_screen.dart';
import 'features/master/master_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  const storage = FlutterSecureStorage();
  final token = await storage.read(key: 'token');
  final role = await storage.read(key: 'role');

  Widget initialScreen = const LoginScreen();
  if (token != null && role != null) {
    if (role == 'master') {
      initialScreen = const MasterScreen();
    } else {
      initialScreen = const HomeScreen();
    }
  }

  runApp(QualityControlApp(initialScreen: initialScreen));
}

class QualityControlApp extends StatelessWidget {
  final Widget initialScreen;
  const QualityControlApp({super.key, required this.initialScreen});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: AppConstants.appTitle,
      theme: AppTheme.lightTheme,
      home: initialScreen,
      debugShowCheckedModeBanner: false,
    );
  }
}
