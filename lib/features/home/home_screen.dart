import 'package:flutter/material.dart';
import '../../core/services/api_service.dart';
import '../report/report_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  final _apiService = ApiService();
  List<dynamic> _requests = [];
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadRequests();
  }

  Future<void> _loadRequests() async {
    setState(() => _isLoading = true);
    final requests = await _apiService.getRequests();
    if (mounted) {
      setState(() {
        _requests = requests;
        _isLoading = false;
      });
    }
  }

  Color _getStatusColor(String status) {
    switch (status) {
      case 'Processed':
        return Colors.green;
      case 'In Progress':
        return Colors.orange;
      case 'Denied':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String _translateStatus(String status) {
    switch (status) {
      case 'Pending':
        return 'Ожидает';
      case 'In Progress':
        return 'В работе';
      case 'Processed':
        return 'Выполнена';
      case 'Denied':
        return 'Отклонена';
      default:
        return status;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Мои заявки'),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: _loadRequests),
        ],
      ),
      body: _isLoading
          ? const Center(child: CircularProgressIndicator())
          : _requests.isEmpty
          ? const Center(child: Text('Нет активных заявок'))
          : ListView.builder(
              padding: const EdgeInsets.all(16),
              itemCount: _requests.length,
              itemBuilder: (context, index) {
                final req = _requests[index];
                return Card(
                  child: ListTile(
                    leading: CircleAvatar(
                      backgroundColor: _getStatusColor(req['status']),
                      child: const Icon(Icons.build, color: Colors.white),
                    ),
                    title: Text('Заявка #${req['id']}'),
                    subtitle: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(req['description'] ?? ''),
                        const SizedBox(height: 4),
                        Text(
                          'Статус: ${_translateStatus(req['status'])}',
                          style: TextStyle(
                            color: _getStatusColor(req['status']),
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () async {
          await Navigator.push(
            context,
            MaterialPageRoute(builder: (context) => const ReportScreen()),
          );
          _loadRequests();
        },
        label: const Text('Создать заявку'),
        icon: const Icon(Icons.add),
      ),
    );
  }
}
