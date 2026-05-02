import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../features/auth/presentation/providers/auth_provider.dart';
import '../../features/auth/presentation/screens/login_screen.dart';
import '../../features/auth/presentation/screens/register_screen.dart';
import '../../features/dashboard/presentation/screens/dashboard_screen.dart';

// Rutas de autenticación (públicas)
const _authRoutes = ['/login', '/register'];

final routerProvider = Provider<GoRouter>((ref) {
  // Notifier que notifica a GoRouter cuando el estado de auth cambia
  final authNotifier = _AuthRouterNotifier(ref);

  return GoRouter(
    initialLocation: '/login',
    refreshListenable: authNotifier,
    redirect: (context, state) {
      final authState = ref.read(authProvider);
      final status = authState.status;
      final location = state.matchedLocation;

      // Mientras se inicializa, no redirigir
      if (status == AuthStatus.initial || status == AuthStatus.loading) {
        return null;
      }

      final isAuthenticated = status == AuthStatus.authenticated;
      final isAuthRoute = _authRoutes.contains(location);

      // Autenticado intentando ir a login/register → dashboard
      if (isAuthenticated && isAuthRoute) return '/dashboard';

      // No autenticado intentando acceder a ruta protegida → login
      if (!isAuthenticated && !isAuthRoute) return '/login';

      return null; // Sin redirección
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      GoRoute(
        path: '/register',
        builder: (context, state) => const RegisterScreen(),
      ),
      GoRoute(
        path: '/dashboard',
        builder: (context, state) => const DashboardScreen(),
      ),
    ],
  );
});

/// Listenable que escucha cambios en authProvider y notifica al GoRouter
/// para que re-evalúe la función redirect.
class _AuthRouterNotifier extends ChangeNotifier {
  _AuthRouterNotifier(Ref ref) {
    ref.listen<AuthState>(authProvider, (_, __) => notifyListeners());
  }
}
