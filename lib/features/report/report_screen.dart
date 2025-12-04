import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/services/api_service.dart';
import '../../core/services/storage_service.dart';

class ReportScreen extends StatefulWidget {
  const ReportScreen({super.key});

  @override
  State<ReportScreen> createState() => _ReportScreenState();
}

class _ReportScreenState extends State<ReportScreen> {
  final _formKey = GlobalKey<FormState>();
  final _idController = TextEditingController();
  final _descriptionController = TextEditingController();
  final _picker = ImagePicker();

  XFile? _image;
  XFile? _video;
  Uint8List? _imageBytes;
  bool _isLoading = false;

  Future<void> _pickMedia(ImageSource source, {bool isVideo = false}) async {
    try {
      XFile? pickedFile;
      if (isVideo) {
        pickedFile = await _picker.pickVideo(
          source: source,
          maxDuration: const Duration(seconds: 30),
        );
      } else {
        pickedFile = await _picker.pickImage(source: source, imageQuality: 50);
      }

      if (pickedFile != null) {
        Uint8List? bytes;
        if (!isVideo) {
          bytes = await pickedFile.readAsBytes();
        }

        setState(() {
          if (isVideo) {
            _video = pickedFile;
            _image = null;
            _imageBytes = null;
          } else {
            _image = pickedFile;
            _imageBytes = bytes;
            _video = null;
          }
        });
      }
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('Ошибка при выборе медиа: $e')));
    }
  }

  Future<void> _showSourceDialog({required bool isVideo}) async {
    final source = await showDialog<ImageSource>(
      context: context,
      builder: (context) => AlertDialog(
        title: Text(
          isVideo ? 'Выберите источник видео' : 'Выберите источник фото',
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt),
              title: const Text('Камера'),
              onTap: () => Navigator.pop(context, ImageSource.camera),
            ),
            ListTile(
              leading: const Icon(Icons.photo_library),
              title: const Text('Галерея'),
              onTap: () => Navigator.pop(context, ImageSource.gallery),
            ),
          ],
        ),
      ),
    );

    if (source != null) {
      _pickMedia(source, isVideo: isVideo);
    }
  }

  Future<void> _submitReport() async {
    if (!_formKey.currentState!.validate()) return;

    setState(() => _isLoading = true);

    final String equipmentId = _idController.text;
    final String description = _descriptionController.text;
    final fullDescription = 'ID: $equipmentId\n$description';

    try {
      final success = await ApiService().createRequest(
        fullDescription,
        _image,
        video: _video,
      );

      if (success) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Заявка успешно отправлена!'),
              backgroundColor: Colors.green,
            ),
          );
          Navigator.pop(context);
        }
      } else {
        throw Exception('Failed to create request');
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Ошибка: $e'),
            backgroundColor: Colors.red,
            duration: const Duration(seconds: 5),
          ),
        );
      }
    } finally {
      if (mounted) {
        setState(() => _isLoading = false);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Новая заявка')),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16.0),
        child: Form(
          key: _formKey,
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Autocomplete<String>(
                optionsBuilder: (TextEditingValue textEditingValue) {
                  if (textEditingValue.text == '') {
                    return const Iterable<String>.empty();
                  }
                  return StorageService.equipmentList.where((String option) {
                    return option.toLowerCase().contains(
                      textEditingValue.text.toLowerCase(),
                    );
                  });
                },
                onSelected: (String selection) {
                  _idController.text = selection;
                },
                fieldViewBuilder:
                    (
                      context,
                      textEditingController,
                      focusNode,
                      onFieldSubmitted,
                    ) {
                      // Sync internal controller with Autocomplete's controller
                      textEditingController.addListener(() {
                        _idController.text = textEditingController.text;
                      });

                      return TextFormField(
                        controller: textEditingController,
                        focusNode: focusNode,
                        decoration: const InputDecoration(
                          labelText: 'ID / Название станка',
                          hintText: 'Начните вводить (например, CNC)',
                          prefixIcon: Icon(Icons.qr_code),
                        ),
                        validator: (value) => value?.isEmpty ?? true
                            ? 'Введите ID оборудования'
                            : null,
                      );
                    },
              ),
              const SizedBox(height: 16),
              TextFormField(
                controller: _descriptionController,
                decoration: const InputDecoration(
                  labelText: 'Описание проблемы',
                  hintText: 'Что случилось?',
                  prefixIcon: Icon(Icons.description),
                  alignLabelWithHint: true,
                ),
                maxLines: 4,
                validator: (value) =>
                    value?.isEmpty ?? true ? 'Опишите проблему' : null,
              ),
              const SizedBox(height: 20),
              if (_imageBytes != null)
                Stack(
                  alignment: Alignment.topRight,
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Image.memory(
                        _imageBytes!,
                        height: 200,
                        width: double.infinity,
                        fit: BoxFit.cover,
                      ),
                    ),
                    IconButton(
                      onPressed: () => setState(() {
                        _image = null;
                        _imageBytes = null;
                      }),
                      icon: const Icon(Icons.close, color: Colors.white),
                      style: IconButton.styleFrom(
                        backgroundColor: Colors.black54,
                      ),
                    ),
                  ],
                ),
              if (_video != null)
                Container(
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: Colors.grey[200],
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: Colors.grey),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.videocam, size: 40, color: Colors.red),
                      const SizedBox(width: 16),
                      const Expanded(
                        child: Text('Видео записано и готово к отправке'),
                      ),
                      IconButton(
                        onPressed: () => setState(() => _video = null),
                        icon: const Icon(Icons.close),
                      ),
                    ],
                  ),
                ),
              const SizedBox(height: 10),
              Row(
                children: [
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () => _showSourceDialog(isVideo: false),
                      icon: const Icon(Icons.photo_camera),
                      label: const Text('ФОТО'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.all(16),
                        backgroundColor: Colors.blue,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: ElevatedButton.icon(
                      onPressed: () => _showSourceDialog(isVideo: true),
                      icon: const Icon(Icons.videocam),
                      label: const Text('ВИДЕО'),
                      style: ElevatedButton.styleFrom(
                        padding: const EdgeInsets.all(16),
                        backgroundColor: Colors.red,
                        foregroundColor: Colors.white,
                      ),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 30),
              SizedBox(
                height: 55,
                child: ElevatedButton(
                  onPressed: _isLoading ? null : _submitReport,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: Colors.blueAccent,
                    foregroundColor: Colors.white,
                  ),
                  child: _isLoading
                      ? const CircularProgressIndicator(color: Colors.white)
                      : const Text('ОТПРАВИТЬ ЗАЯВКУ'),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
