import 'package:dio/dio.dart';
import '../constants/api_constants.dart';
import '../services/token_storage.dart';

class DioClient {
  static final DioClient _instance = DioClient._internal();
  factory DioClient() => _instance;

  late final Dio dio;
  final TokenStorage _tokenStorage = TokenStorage();

  DioClient._internal() {
    dio = Dio(
      BaseOptions(
        baseUrl: ApiConstants.baseUrl,
        connectTimeout: const Duration(seconds: 10),
        receiveTimeout: const Duration(seconds: 10),
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      ),
    );

    dio.interceptors.add(_AuthInterceptor(_tokenStorage, dio));
  }
}

class _AuthInterceptor extends Interceptor {
  final TokenStorage _tokenStorage;
  final Dio _dio;

  _AuthInterceptor(this._tokenStorage, this._dio);

  @override
  Future<void> onRequest(
    RequestOptions options,
    RequestInterceptorHandler handler,
  ) async {
    final token = await _tokenStorage.getAccessToken();
    if (token != null && token.isNotEmpty) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  Future<void> onError(
    DioException err,
    ErrorInterceptorHandler handler,
  ) async {
    if (err.response?.statusCode == 401) {
      final refreshed = await _tryRefreshToken();
      if (refreshed) {
        // Reintentar la petición original con el nuevo access token
        final newToken = await _tokenStorage.getAccessToken();
        final opts = err.requestOptions;
        opts.headers['Authorization'] = 'Bearer $newToken';
        try {
          final response = await _dio.fetch(opts);
          return handler.resolve(response);
        } catch (_) {
          // Si el reintento falla, limpiar tokens
          await _tokenStorage.clearTokens();
        }
      } else {
        await _tokenStorage.clearTokens();
      }
    }
    handler.next(err);
  }

  Future<bool> _tryRefreshToken() async {
    final refreshToken = await _tokenStorage.getRefreshToken();
    if (refreshToken == null || refreshToken.isEmpty) return false;

    try {
      // Usar una instancia Dio sin interceptores para evitar bucles infinitos
      final plainDio = Dio(BaseOptions(baseUrl: ApiConstants.baseUrl));
      final response = await plainDio.post(
        ApiConstants.refresh,
        data: {'refresh': refreshToken},
      );

      final newAccessToken = response.data['access'] as String?;
      final newRefreshToken = response.data['refresh'] as String?;

      if (newAccessToken == null) return false;

      await _tokenStorage.saveAccessToken(newAccessToken);
      if (newRefreshToken != null) {
        await _tokenStorage.saveRefreshToken(newRefreshToken);
      }
      return true;
    } catch (_) {
      return false;
    }
  }
}
