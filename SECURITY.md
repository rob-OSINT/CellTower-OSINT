# Security Policy

## ⚠️ Legal Disclaimer

CellTower-OSINT is intended **strictly** for:

- ✅ Authorized penetration testing on networks you own or have written permission to test
- ✅ Personal RF/signal auditing on your own devices
- ✅ Academic research and education in controlled environments
- ✅ Law enforcement with proper legal authority

**Do NOT use this tool to:**

- ❌ Monitor, track, or intercept communications of individuals without consent
- ❌ Interfere with or disrupt cellular infrastructure
- ❌ Violate local, national, or international telecommunications laws
- ❌ Conduct surveillance without legal authorization

> Misuse of this tool may violate laws including the **Computer Fraud and Abuse Act (CFAA)**, **Electronic Communications Privacy Act (ECPA)**, and equivalent legislation in your jurisdiction. You are solely responsible for your actions.

---

## 🔐 Supported Versions

| Version | Supported |
|---------|-----------|
| 2.0.x   | ✅ Active  |
| 1.x.x   | ❌ Deprecated |

---

## 🐛 Reporting a Vulnerability

If you discover a security vulnerability in this project:

1. **Do NOT open a public GitHub issue**
2. Go to the **[Security tab](../../security/advisories/new)** on this repo
3. Submit a private advisory with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

We aim to respond within **72 hours** and resolve critical issues within **7 days**.

---

## 🛡️ Responsible Disclosure

We follow a **coordinated disclosure** policy:

- Reporter submits vulnerability privately
- Maintainer confirms and investigates
- Fix is developed and tested
- Patch is released
- Vulnerability is publicly disclosed after fix

Credit will be given to reporters in the release notes unless anonymity is requested.

---

## 📋 Scope

| In Scope | Out of Scope |
|----------|--------------|
| Code vulnerabilities in `tower_geo_locator.py` | Third-party APIs (OpenCellID) |
| Insecure data handling or storage | ADB/Android OS bugs |
| API key exposure risks | Network infrastructure issues |
| Dependency vulnerabilities | Social engineering |

---

*This security policy applies to all versions of CellTower-OSINT maintained by rob-OSINT.*
