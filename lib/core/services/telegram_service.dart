import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import '../constants/app_constants.dart';

class TelegramService {
  final String _baseUrl =
      'https://api.telegram.org/bot${AppConstants.telegramBotToken}';

  Future<void> sendMessage(String text) async {
    final url = Uri.parse('$_baseUrl/sendMessage');
    try {
      final response = await http.post(
        url,
        body: {'chat_id': AppConstants.telegramChatId, 'text': text},
      );
      if (response.statusCode != 200) {
        throw Exception(
          'Telegram API Error: ${response.statusCode} ${response.body}',
        );
      }
    } catch (e) {
      debugPrint('Error sending message: $e');
      rethrow;
    }
  }

  Future<void> sendPhoto(XFile photo, String caption) async {
    final url = Uri.parse('$_baseUrl/sendPhoto');
    try {
      final bytes = await photo.readAsBytes();
      final request = http.MultipartRequest('POST', url)
        ..fields['chat_id'] = AppConstants.telegramChatId
        ..fields['caption'] = caption
        ..files.add(
          http.MultipartFile.fromBytes('photo', bytes, filename: photo.name),
        );

      final response = await request.send();
      if (response.statusCode != 200) {
        final respStr = await response.stream.bytesToString();
        throw Exception('Telegram API Error: ${response.statusCode} $respStr');
      }
    } catch (e) {
      debugPrint('Error sending photo: $e');
      rethrow;
    }
  }

  Future<void> sendVideo(XFile video, String caption) async {
    final url = Uri.parse('$_baseUrl/sendVideo');
    try {
      final bytes = await video.readAsBytes();
      final request = http.MultipartRequest('POST', url)
        ..fields['chat_id'] = AppConstants.telegramChatId
        ..fields['caption'] = caption
        ..files.add(
          http.MultipartFile.fromBytes('video', bytes, filename: video.name),
        );

      final response = await request.send();
      if (response.statusCode != 200) {
        final respStr = await response.stream.bytesToString();
        throw Exception('Telegram API Error: ${response.statusCode} $respStr');
      }
    } catch (e) {
      debugPrint('Error sending video: $e');
      rethrow;
    }
  }
}
