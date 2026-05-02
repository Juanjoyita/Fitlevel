class ApiConstants {
  ApiConstants._();

  static const String baseUrl = 'http://localhost:8000/api/v1';

  // Auth endpoints
  static const String login = '/auth/login/';
  static const String register = '/auth/register/';
  static const String refresh = '/auth/refresh/';
  static const String logout = '/auth/logout/';
}
