import Foundation
import Combine

class UserViewModel: ObservableObject {
    @Published var currentUser: User?
    @Published var isAuthenticated = false
    
    func login(username: String, password: String) {
        // Implement login logic
    }
    
    func register(username: String, password: String, bio: String) {
        // Implement registration logic
    }
} 