import SwiftUI

struct ContentView: View {
    @StateObject var connectivity = ConnectivityManager.shared
    
    var body: some View {
        VStack {
            if let message = connectivity.receivedMessage {
                Image(systemName: message.iconName)
                    .resizable()
                    .scaledToFit()
                    .frame(width: 50, height: 50)
                    .foregroundColor(message.isDanger ? .red : .green)
                
                Text(message.title)
                    .font(.system(size: 15, weight: .bold))
            } else {
                ProgressView() // 로딩 애니메이션
                Text("소리 대기 중...")
                    .font(.footnote)
                    .padding(.top, 5)
            }
        }
    }
}
