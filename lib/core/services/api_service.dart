import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:image_picker/image_picker.dart';

class ApiService {
  // Updated to local IP for real device testing
  static const String baseUrl = 'http://10.53.11.141:8000';

  final Dio _dio = Dio(BaseOptions(baseUrl: baseUrl));
  final FlutterSecureStorage _storage = const FlutterSecureStorage();

  Future<String?> login(String username, String password) async {
    try {
      final response = await _dio.post(
        '/auth/login',
        data: {'username': username, 'password': password},
      );

      if (response.statusCode == 200) {
        final token = response.data['token'];
        final userId = response.data['user_id'];
        await _storage.write(key: 'jwt_token', value: token);
        await _storage.write(key: 'user_id', value: userId.toString());
        return null; // Success
      }
    } catch (e) {
      if (e is DioException) {
        if (e.type == DioExceptionType.connectionTimeout ||
            e.type == DioExceptionType.receiveTimeout ||
            e.type == DioExceptionType.connectionError) {
          return 'Ошибка соединения: Проверьте IP и Wi-Fi.\n${e.message}';
        }
        return e.response?.data['detail'] ?? 'Ошибка входа: ${e.message}';
      }
      return 'Произошла ошибка: $e';
    }
    return 'Неизвестная ошибка';
  }

  Future<List<dynamic>> getRequests() async {
    try {
      final userId = await _storage.read(key: 'user_id');
      final response = await _dio.get(
        '/requests',
        queryParameters: {'user_id': userId},
      );
      return response.data;
    } catch (e) {
      debugPrint('Error fetching requests: $e');
      return [];
    }
  }

  Future<bool> createRequest(String description, XFile? photo) async {
    try {
      final userId = await _storage.read(key: 'user_id');

      final Map<String, dynamic> formDataMap = {
        'user_id': userId,
        'description': description,
      };

      if (photo != null) {
        final bytes = await photo.readAsBytes();
        formDataMap['photo'] = MultipartFile.fromBytes(
          bytes,
          filename: photo.name,
        );
      }

      FormData formData = FormData.fromMap(formDataMap);

      final response = await _dio.post('/requests', data: formData);
      return response.statusCode == 200;
    } catch (e) {
      debugPrint('Error creating request: $e');
      return false;
    }
  }
}
