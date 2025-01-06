struct User: Codable, Identifiable {
    let id: Int
    var username: String
    var bio: String
    var isPrivate: Bool
    var joinDate: Date
    var profilePic: String?
} 