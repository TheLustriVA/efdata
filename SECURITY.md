# Security Policy

## Reporting Security Vulnerabilities

If you discover a security vulnerability in EFData, please **DO NOT** create a public GitHub issue.

Instead, please send details to: kieran.bicheno@gmail.com

Include:
- Description of the vulnerability
- Steps to reproduce
- Potential impact
- Suggested fix (if any)

I'll respond within 48 hours and work on a fix immediately.

## Security Measures

EFData implements several security measures:

1. **No hardcoded credentials** - All sensitive data in environment variables
2. **Database connections** - Use SSL where configured
3. **API authentication** - JWT tokens for production deployments
4. **Input validation** - All user inputs sanitized
5. **Dependency scanning** - Regular updates via GitHub Dependabot

## Known Security Considerations

- The application requires database credentials with write access
- Exchange rate API keys should be kept confidential
- Production deployments should use HTTPS
- Database backups may contain sensitive economic data

## Security Checklist for Deployment

- [ ] Change all default passwords
- [ ] Use strong PostgreSQL passwords
- [ ] Enable SSL for database connections
- [ ] Set up firewall rules for database access
- [ ] Use HTTPS for API endpoints
- [ ] Rotate API keys regularly
- [ ] Monitor access logs