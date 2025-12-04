import 'package:flutter/material.dart';
import '../../core/services/api_service.dart';

class WorkerRequestDetailScreen extends StatelessWidget {
  final dynamic request;

  const WorkerRequestDetailScreen({super.key, required this.request});

  Color _getStatusColor(String status) {
    switch (status) {
      case 'Новая':
      case 'Назначена':
        return const Color(0xFF2196F3);
      case 'В работе':
        return const Color(0xFFFF9800);
      case 'Выполнена':
        return const Color(0xFF4CAF50);
      case 'Отклонена':
        return const Color(0xFFF44336);
      default:
        return Colors.grey;
    }
  }

  @override
  Widget build(BuildContext context) {
    final statusColor = _getStatusColor(request['status'] ?? '');
    final photoPath = request['photo_path'];
    final masterName = request['technician_name'];

    return Scaffold(
      appBar: AppBar(
        title: Text('Заявка #${request['id']}'),
        flexibleSpace: Container(
          decoration: const BoxDecoration(
            gradient: LinearGradient(
              colors: [Color(0xFF1565C0), Color(0xFF64B5F6)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
          ),
        ),
      ),
      body: SingleChildScrollView(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            if (photoPath != null)
              Container(
                height: 250,
                width: double.infinity,
                decoration: BoxDecoration(color: Colors.grey[200]),
                child: Image.network(
                  '${ApiService.baseUrl}/$photoPath',
                  fit: BoxFit.cover,
                  errorBuilder: (context, error, stackTrace) => const Center(
                    child: Icon(
                      Icons.broken_image,
                      size: 50,
                      color: Colors.grey,
                    ),
                  ),
                ),
              ),
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Status Badge
                  Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 16,
                      vertical: 8,
                    ),
                    decoration: BoxDecoration(
                      color: statusColor.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(30),
                      border: Border.all(color: statusColor, width: 1.5),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(Icons.info_outline, size: 18, color: statusColor),
                        const SizedBox(width: 8),
                        Text(
                          request['status'] ?? '',
                          style: TextStyle(
                            color: statusColor,
                            fontWeight: FontWeight.bold,
                            fontSize: 16,
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),
                  _buildInfoSection(
                    'Описание',
                    request['description'] ?? 'Нет описания',
                  ),
                  const SizedBox(height: 16),
                  if (masterName != null) ...[
                    _buildInfoSection('Назначенный мастер', masterName),
                    const SizedBox(height: 16),
                  ],
                  _buildInfoSection(
                    'Дата создания',
                    request['created_at']
                            ?.toString()
                            .replaceAll('T', ' ')
                            .split('.')[0] ??
                        '',
                  ),
                  const SizedBox(height: 24),
                  if (request['status'] == 'Выполнена' ||
                      request['status'] == 'Completed')
                    Container(
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: Colors.green.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.check_circle, color: Colors.green),
                          SizedBox(width: 8),
                          Text(
                            'Заявка выполнена',
                            style: TextStyle(
                              color: Colors.green,
                              fontWeight: FontWeight.bold,
                              fontSize: 16,
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildInfoSection(String title, String content) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          title,
          style: TextStyle(
            color: Colors.grey[600],
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          content,
          style: const TextStyle(
            fontSize: 16,
            color: Colors.black87,
            height: 1.4,
          ),
        ),
      ],
    );
  }
}
