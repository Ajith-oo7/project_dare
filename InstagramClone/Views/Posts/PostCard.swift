struct PostCard: View {
    let post: Post
    @EnvironmentObject var postVM: PostViewModel
    
    var body: some View {
        VStack(alignment: .leading) {
            // User info header
            HStack {
                Text(post.username)
                Spacer()
            }
            
            // Media content
            if post.mediaType == .image {
                AsyncImage(url: URL(string: post.mediaPath)) { image in
                    image.resizable()
                        .aspectRatio(contentMode: .fit)
                } placeholder: {
                    ProgressView()
                }
            } else {
                VideoPlayer(url: URL(string: post.mediaPath)!)
            }
            
            // Trend buttons
            HStack {
                Button(action: { postVM.addTrend(post: post, isUptrend: true) }) {
                    Image(systemName: "arrow.up.circle")
                }
                Button(action: { postVM.addTrend(post: post, isUptrend: false) }) {
                    Image(systemName: "arrow.down.circle")
                }
            }
            
            // Caption and comments
            Text(post.caption)
            CommentsView(comments: post.comments)
        }
        .padding()
    }
} 