struct MainTabView: View {
    var body: some View {
        TabView {
            HomeView()
                .tabItem {
                    Label("Home", systemImage: "house")
                }
            SearchView()
                .tabItem {
                    Label("Search", systemImage: "magnifyingglass")
                }
            CreatePostView()
                .tabItem {
                    Label("Post", systemImage: "plus.square")
                }
            StreamView()
                .tabItem {
                    Label("Stream", systemImage: "play.square")
                }
            ProfileView()
                .tabItem {
                    Label("Profile", systemImage: "person")
                }
        }
    }
} 