#include "config_unix.h"
#include "config_win32.h"

#ifndef _RING_BUF_H
#include "ring_buf.h"
#endif

pthread_mutex_t mutex	   = PTHREAD_MUTEX_INITIALIZER;
pthread_cond_t thread_cond = PTHREAD_COND_INITIALIZER;

ring_buffer* ring_buf;

unsigned short getindex;
unsigned short putindex;

unsigned short buffersize;
unsigned short ring_buf_len;

void ring_buf_init(int buf_size)
{
    putindex = 0;
    getindex = 0;
    buffersize = 0;

    ring_buf_len    = buf_size;
    ring_buf	    = (ring_buffer *)malloc(sizeof(ring_buffer) * ring_buf_len);

//  fp = fopen("ringbuf.log", "a");
}

void ring_buf_close(void)
{
    if(ring_buf != NULL) free(ring_buf);
//  if(fp != NULL) fclose(fp);
}

int set_buffer(ring_buffer *buf, uint8_t *data, int data_len, source_info *src)
{
    if(buf->is_filled == 1) return -1;
    
    memcpy(buf->data, data, data_len);
    buf->data_len  = data_len;
    buf->is_filled = 1;

    if( src != NULL ) {
	buf->data_src.src_addr = src->src_addr;
	buf->data_src.src_port = src->src_port;
    }

    return 0;
}

int put_ring( uint8_t *ptr, int ptr_len, source_info *src )
{
    ring_buffer* buf_addr;
    ring_buffer* buf;

    pthread_mutex_lock(&mutex);

    while ( buffersize >= ring_buf_len )
    {
		pthread_cond_wait(&thread_cond, &mutex);
    }

    buf_addr = ring_buf + putindex;
    buf = (ring_buffer *)buf_addr;

    set_buffer(buf, ptr, ptr_len, src);

    putindex++;
    if ( putindex >= ring_buf_len )
	putindex = 0;
    buffersize++;

//    fprintf(fp, "put_ring : %s %d %d %d %d\n", ptr, putindex, getindex, buffersize, ring_buf_len); 
//    fflush(fp);
    
    pthread_cond_signal(&thread_cond);
    pthread_mutex_unlock(&mutex);

    return 0;
}

int get_ring( uint8_t *ptr, source_info *src )
{
    int len = 0;

    ring_buffer* buf_addr;
    ring_buffer* buf;

    pthread_mutex_lock(&mutex);
    
    while(!buffersize) {
		pthread_cond_wait(&thread_cond, &mutex);
    }

    buf_addr = ring_buf + getindex;
    buf      = (ring_buffer *)buf_addr;
	
    if( buf->is_filled == 0) {   
        return -1;
    }

    memcpy(ptr, buf->data, buf->data_len);
    len  = buf->data_len;
    if( src != NULL ) {
		src->src_addr = buf->data_src.src_addr;
		src->src_port = buf->data_src.src_port;
    }

    memset(buf->data, 0, buf->data_len);
    buf->data_len	   = 0;
    buf->data_src.src_addr = 0;
    buf->data_src.src_port = 0;
    buf->is_filled	   = 0;

    buffersize--;
    getindex++;

    if ( getindex >= ring_buf_len) getindex = 0;

    pthread_cond_signal(&thread_cond);
    pthread_mutex_unlock(&mutex);

    return len;
}

/*
void* do_loop(void *data)
{
    int i;
    char *str = "do_loop : Hello";
    char data1[1516];

    for(i = 0;i < 10; i++)
    {
	memcpy(data1, str, strlen(str));
	data1[strlen(str)] = '\0';

	printf("%s %d %d\n", str, getindex, putindex);
	put_ring(data1, strlen(str), NULL);
	sleep(1);
    }
}

void* do_loop1(void *data)
{
    int i;
    char *str = "do_loop1 : Bye";
    char data1[1516];

    for(i = 0;i < 10; i++)
    {
        memcpy(data1, str, strlen(str));
        data1[strlen(str)] = '\0';

	printf("%s\n", str);
        put_ring(data1, strlen(str), NULL);
	sleep(1);
    }
}

void* do_loop2(void *data)
{
    int i;
    char data1[1516];

    for(i = 0;i < 20; i++)
    {
	memset(data1, 0, 1516);

	if(get_ring(data1, NULL) != -1)
	    printf("do_loop2 : %s\n", data1);
	sleep(1);
    }
}
*/
// test execution
/*
int main( int argc, char *argv[])
{
    int		thr_id;
    pthread_t	p_thread[3];

    int		status;

    ring_buf_init(7);

    thr_id = pthread_create(&p_thread[0], NULL, do_loop, NULL);
    sleep(1);
    thr_id = pthread_create(&p_thread[1], NULL, do_loop1, NULL);
    sleep(1);
    thr_id = pthread_create(&p_thread[2], NULL, do_loop2, NULL);
    
    pthread_join(p_thread[0], (void **) &status);
    pthread_join(p_thread[1], (void **) &status);
    pthread_join(p_thread[2], (void **) &status);

    status = pthread_mutex_destroy(&mutex);
    printf("code = %d\n", status);
    
    ring_buf_close();

    return 0;  
}*/
