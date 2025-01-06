struct Post: Codable, Identifiable {
    let id: Int
    let userId: Int
    var mediaPath: String
    var caption: String
    var createdDate: Date
    var trendLevel: Int
    var views: Int
    var mediaType: MediaType
    var isArchived: Bool
    var comments: [Comment]
    var trends: [Trend]
    
    enum MediaType: String, Codable {
        case image
        case video
    }
} 