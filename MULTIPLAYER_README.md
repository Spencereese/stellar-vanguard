# Space Shooter - Multiplayer Mode

This game now supports basic multiplayer functionality allowing multiple players to join the same game session.

## Features Added

### Network Architecture
- **Client-Server Model**: One player hosts the server, others join as clients
- **Real-time Communication**: Player positions, health, and actions are synchronized
- **Automatic State Sync**: Game state is shared between all connected players

### Multiplayer Features
- **Player Visualization**: Other players appear as colored triangles with health bars
- **Real-time Updates**: Player movements and status updates at 30Hz
- **Connection Management**: Automatic handling of player joins/leaves
- **Host/Client Modes**: Choose to host a game or join an existing one

## How to Play Multiplayer

### Starting a Server
1. Launch the game
2. Select "Multiplayer" from the main menu
3. Choose "Host Game"
4. Enter server details (default: localhost:5555)
5. The game will start in multiplayer mode

### Joining a Game
1. Launch the game on another machine/device
2. Select "Multiplayer" from the main menu
3. Choose "Join Game"
4. Enter the server host and port
5. Connect and start playing

### Using the Test Script
A convenience script is provided for testing:

```bash
# Terminal 1: Start server
python multiplayer_test.py server

# Terminal 2: Join as client
python multiplayer_test.py client localhost 5555

# Terminal 3: Join as another client
python multiplayer_test.py client localhost 5555
```

## Technical Implementation

### Network Protocol
- **TCP Sockets**: Reliable connection for game state
- **JSON Messages**: Structured data exchange
- **Message Types**:
  - `connect`: Player joining
  - `disconnect`: Player leaving
  - `player_update`: Position/health sync
  - `game_state`: Initial game state for new players

### Architecture
- **NetworkManager**: Handles all network communication
- **MultiplayerMenuState**: UI for hosting/joining games
- **Renderer**: Draws other players on screen
- **Game Loop**: Integrates network updates with game logic

### Limitations
- **Basic Implementation**: Core multiplayer functionality working
- **No Advanced Features**: Chat, teams, or complex game modes
- **Local Network Only**: Designed for LAN play (can be extended for internet)
- **Simple Collision**: Only local player collisions implemented

## Future Enhancements

Potential improvements for the multiplayer system:
- Internet play support
- Chat system
- Team-based gameplay
- Voice communication
- Advanced anti-cheat
- Matchmaking system
- Spectator mode
- Replays and statistics

## Troubleshooting

### Connection Issues
- Ensure firewall allows the game port (default: 5555)
- Check that server is running before clients try to connect
- Verify correct host IP address for remote connections

### Performance
- Close other network-intensive applications
- Ensure stable network connection
- Reduce graphics settings if experiencing lag

### Common Errors
- "Connection refused": Server not running or wrong port
- "Connection timeout": Network issues or firewall blocking
- "Already connected": Try a different port or restart

## Development Notes

The multiplayer system is built with extensibility in mind:
- Modular network manager can be enhanced
- Message protocol supports additional features
- State synchronization can be expanded
- Client-server architecture allows for dedicated servers

For questions or contributions, refer to the main game codebase.