import 'package:dio/dio.dart';
import '../../../core/constants/api_constants.dart';
import '../../../core/network/dio_client.dart';
import '../../../core/services/token_storage.dart';
import 'models/user_model.dart';

class AuthRepository {
  final Dio _dio;
  final TokenStorage _tokenStorage;

  AuthRepository({
    Dio? dio,
    TokenStorage? tokenStorage,
  })  : _dio = dio ?? DioClient().dio,
        _tokenStorage = tokenStorage ?? TokenStorage();

  /// Registra un nuevo usuario.
  /// Devuelve true si el servidor responde con 201 Created.
  Future<bool> register({
    required String email,
    required String username,
    required String password,
  }) async {
    final response = await _dio.post(
      ApiConstants.register,
      data: {
        'email': email,
        'username': username,
        'password': password,
      },
    );
    return response.statusCode == 201;
  }

  /// Inicia sesión con email y contraseña.
  /// Guarda los tokens y devuelve el UserModel del usuario autenticado.
  Future<UserModel> login({
    required String email,
    required String password,
  }) async {
    final response = await _dio.post(
      ApiConstants.login,
      data: {
        'email': email,
        'password': password,
      },
    );

    final data = response.data as Map<String, dynamic>;

    await _tokenStorage.saveTokens(
      accessToken: data['access'] as String,
      refreshToken: data['refresh'] as String,
    );

    return UserModel.fromJson(data['user'] as Map<String, dynamic>);
  }

  /// Cierra sesión enviando el refresh token al servidor.
  /// Siempre elimina los tokens locales en el bloque finally.
  Future<void> logout() async {
    try {
      final refreshToken = await _tokenStorage.getRefreshToken();
      if (refreshToken != null && refreshToken.isNotEmpty) {
        await _dio.post(
          ApiConstants.logout,
          data: {'refresh': refreshToken},
        );
      }
    } finally {
      await _tokenStorage.clearTokens();
    }
  }

  /// Devuelve true si hay tokens guardados (sesión activa).
  Future<bool> isLoggedIn() async {
    return _tokenStorage.hasTokens();
  }
}
