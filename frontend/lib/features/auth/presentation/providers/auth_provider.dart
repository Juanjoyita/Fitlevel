import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/auth_repository.dart';
import '../../data/models/user_model.dart';

// ---------------------------------------------------------------------------
// AuthStatus
// ---------------------------------------------------------------------------
enum AuthStatus { initial, loading, authenticated, unauthenticated, error }

// ---------------------------------------------------------------------------
// AuthState
// ---------------------------------------------------------------------------
class AuthState {
  final AuthStatus status;
  final UserModel? user;
  final String? errorMessage;

  const AuthState({
    this.status = AuthStatus.initial,
    this.user,
    this.errorMessage,
  });

  AuthState copyWith({
    AuthStatus? status,
    UserModel? user,
    String? errorMessage,
  }) {
    return AuthState(
      status: status ?? this.status,
      user: user ?? this.user,
      errorMessage: errorMessage ?? this.errorMessage,
    );
  }
}

// ---------------------------------------------------------------------------
// AuthNotifier
// ---------------------------------------------------------------------------
class AuthNotifier extends StateNotifier<AuthState> {
  final AuthRepository _repository;

  AuthNotifier(this._repository) : super(const AuthState()) {
    _checkAuthStatus();
  }

  /// Verifica si hay una sesión activa al arrancar la app.
  Future<void> _checkAuthStatus() async {
    final loggedIn = await _repository.isLoggedIn();
    state = AuthState(
      status: loggedIn ? AuthStatus.authenticated : AuthStatus.unauthenticated,
    );
  }

  /// Inicia sesión con email y contraseña.
  Future<void> login({
    required String email,
    required String password,
  }) async {
    state = state.copyWith(status: AuthStatus.loading, errorMessage: null);
    try {
      final user = await _repository.login(email: email, password: password);
      state = AuthState(status: AuthStatus.authenticated, user: user);
    } catch (e) {
      state = AuthState(
        status: AuthStatus.error,
        errorMessage: _parseError(e),
      );
    }
  }

  /// Registra un nuevo usuario.
  Future<void> register({
    required String email,
    required String username,
    required String password,
  }) async {
    state = state.copyWith(status: AuthStatus.loading, errorMessage: null);
    try {
      final success = await _repository.register(
        email: email,
        username: username,
        password: password,
      );
      if (success) {
        // Después del registro, hacer login automáticamente
        await login(email: email, password: password);
      } else {
        state = AuthState(
          status: AuthStatus.error,
          errorMessage: 'Registration failed. Please try again.',
        );
      }
    } catch (e) {
      state = AuthState(
        status: AuthStatus.error,
        errorMessage: _parseError(e),
      );
    }
  }

  /// Cierra sesión.
  Future<void> logout() async {
    state = state.copyWith(status: AuthStatus.loading);
    try {
      await _repository.logout();
    } finally {
      state = const AuthState(status: AuthStatus.unauthenticated);
    }
  }

  /// Extrae el mensaje de error de una excepción Dio o genérica.
  String _parseError(Object e) {
    if (e is Exception) {
      final msg = e.toString();
      // Intenta extraer el mensaje del body de la respuesta Dio
      final match = RegExp(r'"detail":"([^"]+)"').firstMatch(msg);
      if (match != null) return match.group(1)!;
      return msg.replaceFirst('Exception: ', '');
    }
    return 'An unexpected error occurred.';
  }
}

// ---------------------------------------------------------------------------
// Providers
// ---------------------------------------------------------------------------
final authRepositoryProvider = Provider<AuthRepository>((ref) {
  return AuthRepository();
});

final authProvider = StateNotifierProvider<AuthNotifier, AuthState>((ref) {
  final repository = ref.read(authRepositoryProvider);
  return AuthNotifier(repository);
});
