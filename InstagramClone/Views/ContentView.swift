struct ContentView: View {
    @EnvironmentObject var userVM: UserViewModel
    
    var body: some View {
        if userVM.isAuthenticated {
            MainTabView()
        } else {
            AuthenticationView()
        }
    }
} 