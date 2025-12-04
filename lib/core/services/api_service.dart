import 'package:dio/dio.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:image_picker/image_picker.dart';

class ApiService {
  // Production URL from Render
  static const String baseUrl = 'https://qualitycontrol-api.onrender.com';

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
        final role = response.data['role'];
        final fullName = response.data['full_name'];

        await _storage.write(key: 'jwt_token', value: token);
        await _storage.write(key: 'user_id', value: userId.toString());
        await _storage.write(key: 'user_role', value: role);
        await _storage.write(key: 'user_name', value: fullName);
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

  Future<String?> getUserRole() async {
    return await _storage.read(key: 'user_role');
  }

  Future<String?> getUserName() async {
    return await _storage.read(key: 'user_name');
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

  // Master-specific methods
  Future<List<dynamic>> getMasterRequests() async {
    try {
      final userId = await _storage.read(key: 'user_id');
      final role = await _storage.read(key: 'user_role');
      final response = await _dio.get(
        '/requests',
        queryParameters: {'user_id': userId, 'role': role},
      );
      return response.data;
    } catch (e) {
      debugPrint('Error fetching master requests: $e');
      return [];
    }
  }

  Future<bool> updateRequestStatus(int requestId, String newStatus) async {
    try {
      final response = await _dio.post(
        '/requests/$requestId/status',
        data: {'status': newStatus},
      );
      return response.statusCode == 200;
    } catch (e) {
      debugPrint('Error updating request status: $e');
      return false;
    }
  }

  Future<dynamic> getRequestById(int requestId) async {
    try {
      final response = await _dio.get('/requests');
      final List<dynamic> allRequests = response.data;
      return allRequests.firstWhere(
        (req) => req['id'] == requestId,
        orElse: () => null,
      );
    } catch (e) {
      debugPrint('Error fetching request by ID: $e');
      return null;
    }
  }
}
