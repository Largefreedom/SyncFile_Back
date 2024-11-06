## Respository Intro

 This repository maily resolve  problems for a big large file transfer system.  Such as,  
 * IO blocking when handle large file
 * Occur high memory storage when load/save large file. 
 * sync operation block the main thread, 
 * High delay when transfer between client and server, owing to file size is large
 * Without restore when occur errors in file transferring or downloading task
 
As for above problem, we did as below:
* 1, Using chunk_size and buffer ways, adjust streaming write or read strategy to achieve low memory usage
* 2, Divide large file into server small chunk files, speed up the file progressing and transfer with muti-thread.
* 3, When receive a chunk for client, will record the state of chunk, such as size_index,hash of content, file_path. With these state info, it can restore file restore when occur errors.
* 4, Download or transfer progress update, server send state the client via websocket protocol



The repository is only backed end.For front end address,plz visit xxx.