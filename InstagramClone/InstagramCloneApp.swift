import SwiftUI

@main
struct InstagramCloneApp: App {
    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(UserViewModel())
                .environmentObject(PostViewModel())
        }
    }
} 