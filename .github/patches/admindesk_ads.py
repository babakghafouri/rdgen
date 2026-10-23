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
  static final Uri _endpoint = Uri.https(
    'ads.admin98.ir',
    '/api/v1/ads',
    {'placement': 'windows-home-sidebar'},
  );

  final http.Client _client = http.Client();
  Timer? _timer;
  Map<String, dynamic>? _ad;

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
      if (response.statusCode != 200) return _hide();
      final data = jsonDecode(response.body);
      if (data is! Map<String, dynamic> ||
          data['is_active'] != true ||
          data['id'] is! String ||
          !_httpsUrl(data['image_url'])) {
        return _hide();
      }
      if (!mounted) return;
      setState(() => _ad = data);
      final raw = data['refresh_seconds'];
      final seconds = raw is int ? raw.clamp(60, 3600) : 300;
      _timer?.cancel();
      _timer = Timer(Duration(seconds: seconds), _load);
    } catch (_) {
      _hide();
    }
  }

  void _hide() {
    if (mounted && _ad != null) setState(() => _ad = null);
    _timer?.cancel();
    _timer = Timer(const Duration(minutes: 5), _load);
  }

  Future<void> _open() async {
    final value = _ad?['target_url'];
    if (!_httpsUrl(value)) return;
    await launchUrl(Uri.parse(value as String), mode: LaunchMode.externalApplication);
  }

  @override
  void dispose() {
    _timer?.cancel();
    _client.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final ad = _ad;
    if (ad == null) return const SizedBox.shrink();
    return Padding(
      padding: const EdgeInsets.fromLTRB(8, 8, 8, 0),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(10),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: _httpsUrl(ad['target_url']) ? _open : null,
            child: Image.network(
              ad['image_url'] as String,
              height: 90,
              width: double.infinity,
              fit: BoxFit.cover,
              errorBuilder: (_, __, ___) => const SizedBox.shrink(),
            ),
          ),
        ),
      ),
    );
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

widget = "if (isWindows && !isOutgoingOnly) const AdminDeskAdBanner(),"
if widget not in text:
    needle = "buildPasswordBoard(context),"
    pos = text.find(needle)
    if pos < 0:
        raise SystemExit("Could not find password board insertion point")
    end = pos + len(needle)
    indent = text[text.rfind("\n", 0, pos) + 1:pos]
    text = text[:end] + "\n" + indent + widget + text[end:]

home.write_text(text, encoding="utf-8")

p = pubspec.read_text(encoding="utf-8")
if not any(line.lstrip().startswith("http:") for line in p.splitlines()):
    marker = "dependencies:\n"
    if marker not in p:
        raise SystemExit("dependencies section not found")
    p = p.replace(marker, marker + "  http: ^1.2.2\n", 1)
    pubspec.write_text(p, encoding="utf-8")

print("AdminDesk ads patch applied")
