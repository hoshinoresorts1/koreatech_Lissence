// Watch App 쪽 ContentView.swift

//import SwiftUI
//
//struct ContentView: View {
//    var body: some View {
//        VStack {
//            Image(systemName: "globe")
//                .imageScale(.large)
//                .foregroundStyle(.tint)
//            Text("Hello, world!")
//        }
//        .padding()
//    }
//}
//
//#Preview {
//    ContentView()
//}

import SwiftUI

struct ContentView: View {
    // 통신 매니저 연결 (데이터가 들어오면 뷰가 자동 갱신됨)
    @StateObject var connectivity = ConnectivityManager.shared
    
    var body: some View {
        VStack {
            if let message = connectivity.receivedMessage {
                // 데이터가 있을 때 보여줄 화면
                Image(systemName: message.iconName)
                    .resizable()
                    .frame(width: 50, height: 50)
                    .foregroundColor(message.isDanger ? .red : .green)
                
                Text(message.title)
                    .font(.headline)
            } else {
                // 데이터 없을 때
                Text("소리 듣는 중...")
            }
        }
    }
}

//#Preview {
//    ContentView()
//}
