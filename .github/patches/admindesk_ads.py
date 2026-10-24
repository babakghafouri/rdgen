#!/usr/bin/env python3
from pathlib import Path

root = Path(".")
home = root / "flutter/lib/desktop/pages/desktop_home_page.dart"
banner = root / "flutter/lib/desktop/pages/ad_banner.dart"
pubspec = root / "flutter/pubspec.yaml"

if not home.exists():
    raise SystemExit("desktop_home_page.dart not found")

banner.write_text(r'''import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:url_launcher/url_launcher.dart';

class AdminDeskAdBanner extends StatefulWidget {
  const AdminDeskAdBanner({super.key});

  @override
  State<AdminDeskAdBanner> createState() => _AdminDeskAdBannerState();
}

class _AdminDeskAdBannerState extends State<AdminDeskAdBanner> {
  static final Uri _endpoint = Uri.parse('https://admin98.ir/api/ads/');

  final http.Client _client = http.Client();
  Timer? _timer;
  List<Map<String, dynamic>> _ads = [];
  int _index = 0;
  Timer? _rotation;

  @override
  void initState() {
    super.initState();
    _load();
  }

  bool _httpsUrl(dynamic value) {
    if (value is! String) return false;
    final uri = Uri.tryParse(value);
    return uri != null && uri.scheme == 'https' && uri.host.isNotEmpty;
  }

  Future<void> _load() async {
    try {
      final response = await _client.get(_endpoint).timeout(const Duration(seconds: 4));
      if (response.statusCode != 200) {
        _hide();
        return;
      }
      final data = jsonDecode(response.body);
      if (data is! Map<String, dynamic> || data['ads'] is! List) {
        _hide();
        return;
      }
      final ads = data['ads'] as List;
      final valid = ads.whereType<Map<String, dynamic>>().where((ad) =>
          _httpsUrl(ad['image_url']) && _httpsUrl(ad['target_url']));
      if (valid.isEmpty) {
        _hide();
        return;
      }
      if (!mounted) return;
      setState(() { _ads = valid.toList(); _index = 0; });
      _rotation?.cancel();
      if (_ads.length > 1) {
        _rotation = Timer.periodic(const Duration(seconds: 5), (_) {
          if (mounted) setState(() => _index = (_index + 1) % _ads.length);
        });
      }
      const seconds = 300;
      _timer?.cancel();
      _timer = Timer(Duration(seconds: seconds), _load);
    } catch (_) {
      _hide();
    }
  }

  void _hide() {
    if (mounted) setState(() => _ads = []);
    _rotation?.cancel();
    _timer?.cancel();
    _timer = Timer(const Duration(minutes: 5), _load);
  }

  Future<void> _open() async {
    final value = _ads.isEmpty ? null : _ads[_index]['target_url'];
    if (!_httpsUrl(value)) return;
    await launchUrl(Uri.parse(value as String), mode: LaunchMode.externalApplication);
  }

  @override
  void dispose() {
    _timer?.cancel();
    _rotation?.cancel();
    _client.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_ads.isEmpty) return const SizedBox.shrink();
    final ad = _ads[_index];
    return LayoutBuilder(builder: (context, constraints) {
      final width = constraints.maxWidth.isFinite ? constraints.maxWidth : 280.0;
      return Container(
        constraints: const BoxConstraints(minHeight: 180, maxHeight: 520),
        margin: const EdgeInsets.all(8),
        decoration: BoxDecoration(
          color: Theme.of(context).cardColor,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: Theme.of(context).dividerColor),
        ),
        child: Column(mainAxisSize: MainAxisSize.min, children: [
          SizedBox(
            height: (width * 1.15).clamp(160.0, 460.0),
            child: InkWell(
              onTap: _httpsUrl(ad['target_url']) ? _open : null,
              child: Image.network(ad['image_url'] as String,
                fit: BoxFit.contain, width: double.infinity,
                errorBuilder: (_, __, ___) => const Center(child: Icon(Icons.broken_image_outlined))),
            ),
          ),
          if (_ads.length > 1)
            Row(mainAxisAlignment: MainAxisAlignment.center, children: [
              IconButton(onPressed: () => setState(() => _index = (_index - 1 + _ads.length) % _ads.length),
                icon: const Icon(Icons.chevron_left)),
              Text('${_index + 1} / ${_ads.length}'),
              IconButton(onPressed: () => setState(() => _index = (_index + 1) % _ads.length),
                icon: const Icon(Icons.chevron_right)),
            ]),
        ]),
      );
    });
  }
}
''', encoding="utf-8")

text = home.read_text(encoding="utf-8")
imp = "import 'ad_banner.dart';"
if imp not in text:
    lines = text.splitlines()
    last_import = max(i for i, line in enumerate(lines) if line.startswith("import "))
    lines.insert(last_import + 1, imp)
    text = "\n".join(lines) + ("\n" if text.endswith("\n") else "")

# Put the advertising area in the right-hand workspace, never the left sidebar.
# RustDesk 1.5.0 has a buildRightPane() that returns ConnectionPage().
old_right = """  buildRightPane(BuildContext context) {
    return Container(
      color: Theme.of(context).scaffoldBackgroundColor,
      child: ConnectionPage(),
    );
  }"""
new_right = """  buildRightPane(BuildContext context) {
    return LayoutBuilder(builder: (context, constraints) {
      final compact = constraints.maxWidth < 680;
      final connection = const ConnectionPage();
      final ad = const AdminDeskAdBanner();
      return Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
            colors: [
              Theme.of(context).scaffoldBackgroundColor,
              Theme.of(context).colorScheme.primary.withOpacity(0.055),
            ],
          ),
        ),
        child: compact
            ? Column(children: [
                Expanded(child: connection),
                if (isWindows && !bind.isOutgoingOnly())
                  SizedBox(height: 230, child: ad),
              ])
            : Row(children: [
                Expanded(child: connection),
                if (isWindows && !bind.isOutgoingOnly())
                  SizedBox(width: (constraints.maxWidth * 0.35).clamp(210.0, 340.0),
                    child: Center(child: ad)),
              ]),
      );
    });
  }"""
if old_right not in text:
    raise SystemExit("Expected RustDesk 1.5.0 right pane not found; refusing incorrect layout patch")
text = text.replace(old_right, new_right, 1)

home.write_text(text, encoding="utf-8")

p = pubspec.read_text(encoding="utf-8")
if not any(line.lstrip().startswith("http:") for line in p.splitlines()):
    marker = "dependencies:\n"
    if marker not in p:
        raise SystemExit("dependencies section not found")
    p = p.replace(marker, marker + "  http: ^1.2.2\n", 1)
    pubspec.write_text(p, encoding="utf-8")

# Hide the editable ID/Relay/API server settings from the Network page.
# The server address and public key are embedded at build time by admindesk_server.py.
settings = root / "flutter/lib/desktop/pages/desktop_setting_page.dart"
if not settings.exists():
    raise SystemExit("desktop_setting_page.dart not found")
settings_text = settings.read_text(encoding="utf-8")
hide_expr = "final hideServer = true;"
import re
pattern = r"final hideServer\s*=\s*bind\.mainGetBuildinOption\(key:\s*kOptionHideServerSetting\)\s*==\s*'Y';"
if hide_expr not in settings_text:
    settings_text, count = re.subn(pattern, hide_expr, settings_text, count=1)
    if count != 1:
        raise SystemExit("Could not find the server settings visibility control; source layout may have changed")
    settings.write_text(settings_text, encoding="utf-8")

print("AdminDesk ads patch applied")
