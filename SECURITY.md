# 🔒 Security Policy

## Supported Versions

We release patches for security vulnerabilities. Here are the versions currently supported:

| Version | Supported | Status |
|---------|-----------|--------|
| 2.x     | ✅ Yes    | Active development |
| 1.x     | ❌ No     | End of life |

---

## 🛡️ Reporting a Vulnerability

We take security seriously and appreciate your efforts to responsibly disclose your findings.

### How to Report

**Please DO NOT** report security vulnerabilities through public GitHub issues. Instead, please report them via:

1. **Email**: [me@srabon.net](mailto:me@srabon.net)
   - Use "Security Vulnerability - UFI SMS Commander" as the subject line
   - Include as much information as possible

2. **GitHub Security Advisory**:
   - Go to: `https://github.com/srabonbangali/UFI-SMS-Commander/security/advisories/new`
   - Click "Report a vulnerability"
   - Fill in the details

### What to Include

Please include the following information in your report:

- **Type of vulnerability** (e.g., XSS, CSRF, privilege escalation)
- **Full steps to reproduce** the issue
- **Impact** of the vulnerability
- **Version** where you found the vulnerability
- **Any potential fixes** you've identified (if any)
- **Proof of concept** (if possible, without compromising security)

### Response Timeline

| Phase | Timeline |
|-------|----------|
| **Initial Response** | Within 48 hours |
| **Acknowledgment** | Within 3 days |
| **Investigation** | Within 1 week |
| **Fix Development** | Within 2 weeks (depending on severity) |
| **Public Disclosure** | Within 30 days after fix |

---

## 🔐 Security Considerations

### Built-in Security Features

UFI SMS Commander is designed with security in mind:

- **Local-only communication**: All requests stay within your local network
- **No data collection**: We don't collect or transmit any user data
- **Password storage**: Passwords are Base64 encoded (not plain text)
- **Config permissions**: Config file is stored with `600` permissions (owner read/write only)

### Potential Risks

Users should be aware of the following:

1. **Network Exposure**: The app communicates with your router over HTTP (not HTTPS)
   - This is a limitation of the router's API
   - Only use on trusted networks

2. **Password Security**: Your router password is stored locally
   - File location: `~/.zte_sms_manager_config.json`
   - Permissions: `chmod 600` to restrict access

3. **Local Access**: Anyone with access to your machine can use the app
   - Ensure your machine is physically secure

### Recommendations for Users

To maximize security:

1. **Use a strong password** for your router
2. **Change default credentials** immediately
3. **Keep your router firmware updated**
4. **Use a firewall** to restrict access to your router
5. **Run the app on trusted networks only**

---

## 📋 Security Best Practices

### For Developers

If you're contributing to UFI SMS Commander:

1. **Never hardcode credentials** in the source code
2. **Use environment variables** for sensitive data
3. **Sanitize all user input** before sending to router
4. **Test for vulnerabilities** before submitting PRs
5. **Follow the principle of least privilege**

### Code Review Checklist

- [ ] No credentials in code
- [ ] Input validation implemented
- [ ] Error handling doesn't leak sensitive info
- [ ] Dependencies are up-to-date
- [ ] No debug code in production

---

## 🚨 Known Issues

### Current Limitations

| Issue | Status | Workaround |
|-------|--------|------------|
| HTTP only (no HTTPS) | Router limitation | Use on trusted networks |
| Password stored in Base64 | Security risk | Set `chmod 600` on config file |
| No rate limiting | Could be abused | Use responsibly |

---

## 📊 Security Update Policy

### Vulnerability Severity Levels

| Severity | Response Time | Action |
|----------|---------------|--------|
| **Critical** | Immediate | Emergency patch within 24 hours |
| **High** | 48 hours | Patch within 3 days |
| **Medium** | 1 week | Patch within 2 weeks |
| **Low** | 2 weeks | Patch in next release |

### Disclosure Policy

1. **Private disclosure**: We'll work with you to fix the issue
2. **Public disclosure**: After fix is released and users have time to update
3. **Credit**: We'll acknowledge your contribution (if desired)

---

## 📝 Reporting Process

### Step-by-Step Guide

1. **Submit Report** via email or GitHub Security Advisory
2. **Receive Acknowledgment** within 48 hours
3. **Collaborate** with our team on the fix
4. **Verification** of the fix
5. **Release** of the security patch
6. **Public Disclosure** (if applicable)

---

## 🌐 External Resources

- [CWE - Common Weakness Enumeration](https://cwe.mitre.org/)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [GitHub Security Advisories](https://docs.github.com/en/code-security/security-advisories)

---

## 👨‍💻 Contact

**Security Team**
- **Email**: me@srabon.net
- **PGP Key**: [Available on request]
- **GitHub**: [@srabonbangali](https://github.com/srabonbangali)

---

## 📜 License

This security policy is licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

---

## 🙏 Acknowledgments

We'd like to thank the following security researchers who have helped make UFI SMS Commander safer:

*This list will be updated as vulnerabilities are responsibly disclosed.*

---

**Version**: 1.0  
**Last Updated**: July 5, 2026  
**Effective Date**: July 5, 2026

---

## 🔄 Change Log

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-07-05 | Initial security policy |

---

**UFI SMS Commander - Security First** 🔒
