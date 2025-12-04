import 'package:flutter/material.dart';
import '../../core/services/api_service.dart';
import '../../core/widgets/video_player_widget.dart';

class RequestDetailScreen extends StatefulWidget {
  final dynamic request;

  const RequestDetailScreen({super.key, required this.request});

  @override
  State<RequestDetailScreen> createState() => _RequestDetailScreenState();
}

class _RequestDetailScreenState extends State<RequestDetailScreen> {
  final _apiService = ApiService();
  late dynamic _request;
  bool _isUpdating = false;

  bool _isVideo(String path) {
    final ext = path.split('.').last.toLowerCase();
    return ['mp4', 'mov', 'avi', 'mkv', 'webm'].contains(ext);
  }

  @override
  void initState() {
    super.initState();
    _request = widget.request;
  }

  Future<void> _updateStatus(String newStatus) async {
    setState(() => _isUpdating = true);

    final success = await _apiService.updateRequestStatus(
      _request['id'],
      newStatus,
    );

    if (mounted) {
      setState(() => _isUpdating = false);
      if (success) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Статус успешно обновлен'),
            backgroundColor: Colors.green,
          ),
        );
        Navigator.pop(context); // Return to list to refresh
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Ошибка обновления статуса'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'New':
      case 'Assigned':
        return Colors.blue;
      case 'In Progress':
        return Colors.orange;
      case 'Processed':
      case 'Completed':
        return Colors.green;
      case 'Denied':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _translateStatus(String status) {
    switch (status) {
      case 'New':
        return 'Новая';
      case 'Assigned':
        return 'Назначена';
      case 'In Progress':
        return 'В работе';
      case 'Processed':
      case 'Completed':
        return 'Выполнена';
      case 'Denied':
        return 'Отклонена';
      default:
        return status;
    }
  }

  @override
  Widget build(BuildContext context) {
    final status = widget.request['status'];
    final statusColor = _getStatusColor(status);
    final statusText = _translateStatus(status);
    final photoPath = widget.request['photo_path'];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Детали заявки'),
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
              _isVideo(photoPath)
                  ? Container(
                      height: 250,
                      width: double.infinity,
                      color: Colors.black,
                      child: VideoPlayerWidget(
                        videoUrl: '${ApiService.baseUrl}/$photoPath',
                      ),
                    )
                  : Container(
                      height: 250,
                      width: double.infinity,
                      decoration: BoxDecoration(color: Colors.grey[200]),
                      child: GestureDetector(
                        onTap: () {
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (context) => Scaffold(
                                appBar: AppBar(
                                  backgroundColor: Colors.black,
                                  iconTheme: const IconThemeData(
                                    color: Colors.white,
                                  ),
                                ),
                                backgroundColor: Colors.black,
                                body: Center(
                                  child: InteractiveViewer(
                                    child: Image.network(
                                      '${ApiService.baseUrl}/$photoPath',
                                      fit: BoxFit.contain,
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          );
                        },
                        child: Image.network(
                          '${ApiService.baseUrl}/$photoPath',
                          fit: BoxFit.cover,
                          errorBuilder: (context, error, stackTrace) =>
                              const Center(
                                child: Icon(
                                  Icons.broken_image,
                                  size: 50,
                                  color: Colors.grey,
                                ),
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
                          statusText,
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
                    _request['description'] ?? 'Нет описания',
                  ),
                  const SizedBox(height: 16),
                  _buildInfoSection(
                    'Автор',
                    _request['author_name'] ?? 'Неизвестно',
                  ),
                  const SizedBox(height: 16),
                  _buildInfoSection(
                    'Дата создания',
                    _request['created_at']
                            ?.toString()
                            .replaceAll('T', ' ')
                            .split('.')[0] ??
                        '',
                  ),

                  const SizedBox(height: 40),

                  if (_request['status'] == 'Назначена' ||
                      _request['status'] == 'Assigned')
                    _buildActionButton(
                      'Принять в работу',
                      Colors.orange,
                      Icons.play_arrow,
                      () => _updateStatus('In Progress'),
                    ),

                  if (_request['status'] == 'В работе' ||
                      _request['status'] == 'In Progress')
                    _buildActionButton(
                      'Завершить работу',
                      Colors.green,
                      Icons.check_circle,
                      () => _updateStatus('Completed'),
                    ),

                  if (_request['status'] == 'Выполнена' ||
                      _request['status'] == 'Completed')
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
                            'Работа завершена',
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

  Widget _buildActionButton(
    String label,
    Color color,
    IconData icon,
    VoidCallback onPressed,
  ) {
    return SizedBox(
      height: 56,
      child: ElevatedButton(
        onPressed: _isUpdating ? null : onPressed,
        style: ElevatedButton.styleFrom(
          backgroundColor: color,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          elevation: 4,
        ),
        child: _isUpdating
            ? const CircularProgressIndicator(color: Colors.white)
            : Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(icon),
                  const SizedBox(width: 12),
                  Text(
                    label,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ],
              ),
      ),
    );
  }
}
